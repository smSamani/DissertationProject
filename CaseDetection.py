
import os
import json
import pandas as pd
import numpy as np
from collections import Counter
from math import sqrt, acos, degrees

# === CONSTANTS ===
TEAM_ID_LEVERKUSEN = 904

# === PIPELINE FUNCTION ===
def run_full_pipeline(event_json_path, match_name):
    """
    Run the full feature extraction pipeline for a single match.
    Returns the final DataFrame for that match.
    """
    try:
        # --- Load events ---
        with open(event_json_path, 'r') as f:
            events = json.load(f)
        HORW = 1 if '_Home' in match_name else 0

        # --- Attack case detection ---
        def find_attack_cases(events):
            cases = []
            case_number = 1

            for i, event in enumerate(events):
                # check if this is a shot with xG by Bayer Leverkusen
                if (
                    event.get("type", {}).get("name") == "Shot"
                    and event.get("team", {}).get("id") == TEAM_ID_LEVERKUSEN
                    and "shot" in event
                    and "statsbomb_xg" in event["shot"]
                ):
                    xg = event["shot"]["statsbomb_xg"]
                    end_point_id = event["id"]
                    end_index = event.get("index")

                    # backtrack to find the last non-Leverkusen possession event
                    start_point_id = None
                    start_index = None
                    for j in range(i - 1, -1, -1):
                        prev_event = events[j]
                        if prev_event.get("possession_team", {}).get("id") != TEAM_ID_LEVERKUSEN:
                            candidate_start_idx = j + 1
                            if candidate_start_idx < len(events):
                                # Collect all substitutions in this attack window
                                substitution_events = [
                                    e for e in events[candidate_start_idx:i+1]
                                    if e.get("type", {}).get("name") == "Substitution" and
                                       e.get("team", {}).get("id") == TEAM_ID_LEVERKUSEN
                                ]
                                if substitution_events:
                                    # Use the earliest substitution event as the true start
                                    earliest_sub = substitution_events[0]
                                    start_point_id = earliest_sub.get("id")
                                    start_index = earliest_sub.get("index")
                                else:
                                    start_point_id = events[candidate_start_idx].get("id")
                                    start_index = events[candidate_start_idx].get("index")
                            break

                    if start_point_id is not None and start_index is not None:
                        cases.append([
                            case_number,
                            match_name,
                            HORW,
                            end_point_id,
                            start_point_id,
                            xg,
                            start_index,
                            end_index
                        ])
                        case_number += 1
            return cases

        attack_cases = find_attack_cases(events)
        if not attack_cases:
            print(f"⚠️ No attack cases detected for {match_name}")
            return pd.DataFrame()

        # --- Clean attack cases ---
        df = pd.DataFrame(attack_cases, columns=["Case number", "Match Name", "HorW", "end_point_id", "start_point_id", "XG", "start_index", "end_index"])
        df['XG'] = pd.to_numeric(df['XG'], errors='coerce')

        def consolidate(group):
            idx_last = group['end_index'].idxmax()
            row = group.loc[idx_last].copy()
            row['XG'] = group['XG'].sum()
            row['num_shots'] = len(group)
            return row

        df_cleaned = df.groupby('start_index', as_index=False).apply(consolidate)
        df_cleaned = df_cleaned.sort_values('Case number').reset_index(drop=True)
        cols = ["Case number", "Match Name", "HorW", "end_point_id", "start_point_id", "XG", "start_index", "end_index", "num_shots"]
        df_cleaned = df_cleaned[cols]

        # --- Base Features ---
        event_index_map = {e["index"]: e for e in events if "index" in e}
        def get_attack_events(start_idx, end_idx):
            return [event_index_map[i] for i in range(start_idx, end_idx+1) if i in event_index_map]
        def safe_duration(e):
            return float(e.get("duration", 0.0)) if "duration" in e and e["duration"] is not None else 0.0
        def pass_length(e):
            if e["type"]["name"] == "Pass":
                return float(e.get("pass", {}).get("length", 0.0))
            return 0.0
        def carry_distance(e):
            if e["type"]["name"] == "Carry":
                loc = e.get("location")
                end_loc = e.get("carry", {}).get("end_location")
                if isinstance(loc, list) and isinstance(end_loc, list) and len(loc) == 2 and len(end_loc) == 2:
                    return sqrt((loc[0] - end_loc[0])**2 + (loc[1] - end_loc[1])**2)
            return 0.0
        def involved_players(e):
            if e.get("team", {}).get("name") == "Bayer Leverkusen":
                return e.get("player", {}).get("id")
            return None
        def is_pass(e):
            return e["type"]["name"] == "Pass"
        durations = []
        distances = []
        num_players = []
        num_passes = []
        for _, row in df_cleaned.iterrows():
            start_idx = int(row["start_index"])
            end_idx = int(row["end_index"])
            events_in_case = get_attack_events(start_idx, end_idx)
            durations.append(sum(safe_duration(e) for e in events_in_case))
            d_pass = sum(pass_length(e) for e in events_in_case)
            d_carry = sum(carry_distance(e) for e in events_in_case)
            distances.append(d_pass + d_carry)
            players = set()
            for e in events_in_case:
                pid = involved_players(e)
                if pid is not None:
                    players.add(pid)
            num_players.append(len(players))
            num_passes.append(sum(1 for e in events_in_case if is_pass(e)))
        df_cleaned["duration"] = durations
        df_cleaned["distance_covered"] = distances
        df_cleaned["number_of_players_involved"] = num_players
        df_cleaned["num_pass"] = num_passes
        BaseFeatures_DF = df_cleaned

        # --- Location Features ---
        events_by_index = {e['index']: e for e in events if 'index' in e}
        df = BaseFeatures_DF.copy()
        def get_zone_number(x, y):
            if not (0 <= x <= 120 and 0 <= y <= 80):
                return None
            zone_x = int(x // 20)
            zone_y = int(y // 20)
            return zone_x * 4 + zone_y + 1
        zone_count_cols = [f'zone_{z}_count' for z in range(1, 25)]
        for col in zone_count_cols:
            df[col] = 0
        df['Start_Zone'] = None
        df['End_Zone'] = None
        df['zone_transition_count'] = 0
        df['forward_movement_count'] = 0
        df['backward_movement_count'] = 0
        df['net_progress_ratio'] = None
        for idx, row in df.iterrows():
            try:
                start_idx = int(row['start_index'])
                end_idx = int(row['end_index'])
            except Exception:
                continue
            evs = [events_by_index[i] for i in range(start_idx, end_idx + 1) if i in events_by_index]
            zone_counts = Counter()
            for ev in evs:
                loc = ev.get('location')
                if loc and isinstance(loc, list) and len(loc) == 2:
                    zone = get_zone_number(loc[0], loc[1])
                    if zone:
                        zone_counts[zone] += 1
            for z in range(1, 25):
                df.at[idx, f'zone_{z}_count'] = int(zone_counts[z])
            zone_sequence = []
            for ev in evs:
                loc = ev.get('location')
                if loc and isinstance(loc, list) and len(loc) == 2:
                    zone = get_zone_number(loc[0], loc[1])
                    if zone is not None:
                        zone_sequence.append(zone)
            transitions = 0
            if len(zone_sequence) >= 2:
                prev_zone = zone_sequence[0]
                for curr_zone in zone_sequence[1:]:
                    if curr_zone != prev_zone:
                        transitions += 1
                        prev_zone = curr_zone
            df.at[idx, 'zone_transition_count'] = transitions
            x_sequence = []
            for ev in evs:
                loc = ev.get('location')
                if loc and isinstance(loc, list) and len(loc) == 2:
                    x_sequence.append(loc[0])
            forward_count = 0
            backward_count = 0
            if len(x_sequence) >= 2:
                for curr_x, next_x in zip(x_sequence[:-1], x_sequence[1:]):
                    if next_x > curr_x:
                        forward_count += 1
                    elif next_x < curr_x:
                        backward_count += 1
            df.at[idx, 'forward_movement_count'] = forward_count
            df.at[idx, 'backward_movement_count'] = backward_count
            forward_distance = 0
            backward_distance = 0
            if len(x_sequence) >= 2:
                for curr_x, next_x in zip(x_sequence[:-1], x_sequence[1:]):
                    delta = next_x - curr_x
                    if delta > 0:
                        forward_distance += delta
                    elif delta < 0:
                        backward_distance += -delta
            denominator = forward_distance + backward_distance
            if denominator > 0:
                ratio = forward_distance / denominator
            else:
                ratio = None
            df.at[idx, 'net_progress_ratio'] = ratio
            start_zone = None
            for ev in evs:
                loc = ev.get('location')
                if loc and isinstance(loc, list) and len(loc) == 2:
                    start_zone = get_zone_number(loc[0], loc[1])
                    break
            end_zone = None
            for ev in reversed(evs):
                loc = ev.get('location')
                if loc and isinstance(loc, list) and len(loc) == 2:
                    end_zone = get_zone_number(loc[0], loc[1])
                    break
            df.at[idx, 'Start_Zone'] = start_zone
            df.at[idx, 'End_Zone'] = end_zone
        df[zone_count_cols] = df[zone_count_cols].fillna(0).astype(int)
        LocationFeatures_DF = df

        # --- Freeze Frame Features ---
        df = LocationFeatures_DF.copy()
        def get_event_by_index(events, idx):
            for ev in events:
                if ev.get("index") == idx:
                    return ev
            return None
        GOAL_X = 120
        GOAL_Y = 40
        GOAL_WIDTH_REAL = 7.32
        PITCH_WIDTH_REAL = 68
        PITCH_WIDTH_SB = 80
        goal_width_sb = GOAL_WIDTH_REAL * (PITCH_WIDTH_SB / PITCH_WIDTH_REAL)
        LEFT_POST = (GOAL_X, GOAL_Y - goal_width_sb / 2)
        RIGHT_POST = (GOAL_X, GOAL_Y + goal_width_sb / 2)
        GOAL_WIDTH = goal_width_sb
        def euclidean_distance(x1, y1, x2, y2):
            return sqrt((x1 - x2)**2 + (y1 - y2)**2)
        def compute_shoot_angle(shooter_x, shooter_y):
            A = euclidean_distance(shooter_x, shooter_y, *LEFT_POST)
            B = euclidean_distance(shooter_x, shooter_y, *RIGHT_POST)
            C = GOAL_WIDTH
            cos_angle = max(-1, min(1, (A**2 + B**2 - C**2) / (2 * A * B)))
            angle_rad = acos(cos_angle)
            return degrees(angle_rad)
        def extract_minute(ts):
            parts = ts.split(':')
            if len(parts) == 2:
                return int(parts[0]) + float(parts[1]) / 60
            elif len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + float(parts[2]) / 60
            else:
                return np.nan
        num_opponents_front_list = []
        distance_to_goal_list = []
        shoot_angle_list = []
        period_list = []
        minute_absolute_list = []
        for _, row in df.iterrows():
            end_idx = int(row["end_index"])
            event = get_event_by_index(events, end_idx)
            num_opponents_front = np.nan
            distance_to_goal = np.nan
            shoot_angle = np.nan
            period = np.nan
            minute_absolute = np.nan
            if event and event.get("type", {}).get("name") == "Shot":
                location = event.get("location")
                if location and len(location) >= 2:
                    shooter_x, shooter_y = location[:2]
                    freeze_frame = event.get("shot", {}).get("freeze_frame")
                    count = 0
                    if freeze_frame:
                        for player in freeze_frame:
                            p_loc = player.get("location")
                            if (p_loc and len(p_loc) >= 2
                                and not player.get("teammate", True)
                                and p_loc[0] > shooter_x
                                and abs(p_loc[1] - shooter_y) <= 0.1 * shooter_y):
                                count += 1
                    num_opponents_front = count
                    distance_to_goal = euclidean_distance(shooter_x, shooter_y, GOAL_X, GOAL_Y)
                    shoot_angle = compute_shoot_angle(shooter_x, shooter_y)
            if event:
                period = event.get("period", np.nan)
                timestamp = event.get("timestamp", None)
                if timestamp is not None:
                    minute = extract_minute(timestamp)
                    if period == 1:
                        minute_absolute = minute
                    elif period == 2:
                        minute_absolute = minute + 45
                    else:
                        minute_absolute = np.nan
            num_opponents_front_list.append(num_opponents_front)
            distance_to_goal_list.append(distance_to_goal)
            shoot_angle_list.append(shoot_angle)
            period_list.append(period)
            minute_absolute_list.append(minute_absolute)
        df["num_opponents_front"] = num_opponents_front_list
        df["distance_to_goal"] = distance_to_goal_list
        df["shoot_angle"] = shoot_angle_list
        df["period"] = period_list
        df["minute_absolute"] = minute_absolute_list
        FreezeFrameFeatures_DF = df
        return FreezeFrameFeatures_DF
    except Exception as e:
        print(f"❌ Error in pipeline for {match_name}: {e}")
        return pd.DataFrame()

# === MULTI-MATCH PIPELINE EXECUTION ===
if __name__ == "__main__":
    BASE_MATCHES_DIR = "/Users/soroushsamani/Desktop/dissertation Data Test/Leverkusen_Matches"
    FINAL_OUTPUT_PATH = "/Users/soroushsamani/Desktop/dissertation Data Test/MatchesData/BaseFeatures.csv"
    all_dfs = []
    matches_processed = 0
    total_attacks = 0
    for match_folder in sorted(os.listdir(BASE_MATCHES_DIR)):
        folder_path = os.path.join(BASE_MATCHES_DIR, match_folder)
        event_json_path = os.path.join(folder_path, "event.json")
        if os.path.isdir(folder_path) and os.path.isfile(event_json_path):
            print(f"➡️ Processing match: {match_folder}")
            df = run_full_pipeline(event_json_path, match_folder)
            if df is not None and not df.empty:
                all_dfs.append(df)
                matches_processed += 1
                total_attacks += len(df)
            else:
                print(f"⚠️ No valid data for {match_folder}")
        else:
            print(f"Skipping {match_folder}: event.json not found.")
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        # Reset "Case number" column so it runs from 1 to N, in order from top to bottom
        final_df["Case number"] = range(1, len(final_df) + 1)
        os.makedirs(os.path.dirname(FINAL_OUTPUT_PATH), exist_ok=True)
        final_df.to_csv(FINAL_OUTPUT_PATH, index=False)
        print(f"\n✅ Processed {matches_processed} matches.")
        print(f"✅ Total attacks: {len(final_df)}")
        print("\nFirst 3 rows of the final DataFrame:")
        print(final_df.head(3))
    else:
        print("❌ No matches processed successfully.")