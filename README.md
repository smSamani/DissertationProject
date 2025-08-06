# Project Progress Summary – Feature Engineering

## Data Selection & Scope

We selected the open-access StatsBomb dataset as our primary data source, focusing specifically on Bayer Leverkusen’s full season in the Bundesliga. This dataset provides highly detailed event logs (`event.json`) for each match. All features in this project were engineered solely from the event.json files, which include both event and freeze-frame (shot context) data. To ensure future flexibility and easy access, we organized the data so that each match has its own folder containing all relevant files.

## Structuring Attack Cases

To prepare the data for feature engineering, we first needed to define and detect individual attacking cases. For this, we identified each Bayer Leverkusen shot (where a valid xG value was present) as the endpoint of an attack. We then backtracked from each shot event to the previous change of possession, which was marked as the start of the attack. In situations where multiple shots occurred within a single possession, these were merged into one case, and the total xG was summed. This process generated a clean dataset of attack cases, each with its own unique start and end points, xG value, and other metadata.

## Phase 1: Basic Statistical Features

In the first phase of feature engineering, we extracted four core statistical features from each attacking case:

- **Duration:** Total active play time during the attack (by summing event durations within each case).
- **Distance Covered:** Combined the length of all passes and the distance of carries to estimate total ball movement.
- **Number of Passes:** Counted the number of pass events in each sequence.
- **Number of Players Involved:** Counted unique Bayer Leverkusen players participating in the attack, with logic to handle substitutions correctly and avoid inflated counts.

These features provide a foundational summary of each attack and form the basis for further tactical analysis.

## Phase 2: Spatial and Ball Progression Features

In the second phase, we focused on the spatial dynamics of each attack by analyzing how the ball moved across different areas of the pitch. The field was divided into a 6x4 grid (24 zones), and we counted the number of times the ball entered each zone during an attack. We also recorded the starting and ending zones for each case. Additional features included the number of zone transitions (how often the ball changed areas), counts of forward and backward movements based on x-coordinate changes, and the net progress ratio—a metric that quantifies how efficiently the ball moved forward compared to backward during the attack.

**Net Progress Ratio = Total Forward Distance ÷ (Total Forward Distance + Total Backward Distance)**

## Phase 3: Freeze Frame and Shot Context Features

In the third phase, we used StatsBomb’s freeze-frame data (included in event.json) to extract spatial context features at the moment of each shot. These include:

- **Number of Opponents in Front:** Counts the defenders directly in front of the shooter—specifically, opponents whose x-coordinate is greater than the shooter’s (closer to goal) and whose y-coordinate is within ±10% of the shooter’s y (roughly in line horizontally).
- **Distance to Goal Center:** The straight-line (Euclidean) distance from the shooter to the center of the goal.
- **Shot Angle:** The size of the open angle to the goal, calculated using the shooter’s position and the goalposts.
- **Match Period:** Whether the shot occurred in the first or second half.
- **Absolute Minute:** The actual minute of the match in which the shot happened (e.g., 54th minute).

These features help quantify the difficulty and quality of the shooting opportunity, providing important context for xG prediction.

## Additional Engineered Features

To provide a more nuanced view of each attack and enrich tactical analysis, several additional features were engineered from the event data, including:

- **Number of Dribbles:** Total dribbles in the attack.
- **Number of Duels:** Total duels in the attack.
- **Number of Crosses:** Total crosses in the attack.
- **Number of Events:** Total number of events in the attack.
- **Goal Scored:** Binary indicator (1 if attack led to a goal, 0 otherwise).
- **Number of Long Passes:** Passes exceeding 30 units in length within the attack.
- **Attack Velocity:** Average ball velocity, calculated as total distance covered divided by attack duration.

## Feature Inventory

Below is the complete list of 24 key features engineered for each attacking case:

1. **Duration**  
2. **Distance Covered**  
3. **Number of Passes**  
4. **Number of Players Involved**  
5. **Zone Entry Counts** (24 zones as a vector)  
6. **Starting Zone**  
7. **Ending Zone**  
8. **Zone Transitions**  
9. **Forward Movements**  
10. **Backward Movements**  
11. **Net Progress Ratio**  
12. **Number of Opponents in Front**  
13. **Distance to Goal Center**  
14. **Shot Angle**  
15. **Match Period**  
16. **Absolute Minute**  
17. **Number of Dribbles**  
18. **Number of Duels**  
19. **Number of Crosses**  
20. **Number of Events**  
21. **Goal Scored**  
22. **Number of Long Passes**  
23. **Attack Velocity**  
24. **Pressure on Shooter** (sum of proximity-weighted defensive presence within 6m at shot moment)

*Note: All features were derived from the event.json file, including freeze-frame information.*

---

Let me know if you want it in a different style (e.g., a more compact table, or extra technical detail for each feature)!