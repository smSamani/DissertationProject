# Bayer Leverkusen Attack Feature Engineering (StatsBomb Data)

## Overview

This project leverages the open-access **StatsBomb football analytics dataset** to engineer advanced features from Bayer Leverkusen’s full Bundesliga season. Our objective: to create a rich dataset of attacking sequences for use in tactical modeling and expected goals (xG) prediction.

We combine granular event logs, lineup data, and freeze-frame spatial context to extract features that go beyond basic stats—enabling deeper, model-driven football analysis.

---

## Data Structure

- **Source:** [StatsBomb Open Data](https://statsbomb.com/)
- **Scope:** All Bundesliga matches for Bayer Leverkusen, one season
- **Organization:**  
  ```
  /MatchFolder/
    ├── event.json
    ├── lineup.json
    └── 360.json
  ```

---

## Methodology

### 1. Structuring Attack Cases

- **Attack Definition:**  
  Each attack ends with a Bayer Leverkusen shot (with valid xG), and starts at the last possession change before the shot.
- **Special Handling:**  
  Multiple shots in one possession are merged; their xG values are summed.
- **Output:**  
  Clean attack cases with unique start/end, summed xG, and all metadata.

---

### 2. Feature Engineering Phases

#### **Phase 1: Basic Statistical Features**
- **Duration:** Total play time in the attack.
- **Distance Covered:** Sum of pass lengths and carries.
- **Number of Passes:** Count of pass events per attack.
- **Players Involved:** Unique Leverkusen players (with correct handling for substitutions).

#### **Phase 2: Spatial & Ball Progression Features**
- **Pitch Grid:** Field divided into a 6x4 grid (24 zones).
- **Zone Features:**  
  - Entry counts per zone  
  - Start/end zone IDs  
  - Number of zone transitions  
  - Forward/backward movement counts  
  - **Net Progress Ratio:**  
    ```
    Net Progress Ratio = Total Forward Distance /
                         (Total Forward Distance + Total Backward Distance)
    ```
    Quantifies forward efficiency during each attack.

#### **Phase 3: Freeze Frame & Shot Context Features**
- **Number of Opponents in Front:**  
  Defenders directly in front, defined as:
  - Opponent (not teammate)
  - X > shooter’s X (closer to goal)
  - Y within ±10% of shooter’s Y (horizontally aligned)
- **Distance to Goal Center:** Euclidean distance from shooter to goal center.
- **Shot Angle:** Open angle to the goal, calculated from shooter position and goalposts.
- **Match Period:** First or second half.
- **Absolute Minute:** Actual minute of the match at shot.

---

## Outputs

- **Final Dataset:**  
  One row per attack, with all engineered features and contextual metadata.
- **Applications:**  
  - xG modeling
  - Clustering of attack types
  - Tactical sequence mining

---

## Innovation & Value

- **Granular context:** Integrates raw event data, player context, and spatial snapshots at the moment of each shot.
- **Flexible structure:** Data is organized for scalable analysis across matches, teams, and competitions.
- **Model-ready:** Engineered features enable sophisticated ML applications, not just summary stats.

---

## Usage

1. **Place StatsBomb data** in the structured folders as shown.
2. **Run the feature extraction pipeline** to generate the final CSV.
3. **Plug the dataset** into your favorite ML or analytics workflow.

---

## Contact

For questions, collaboration, or consulting:  
**Soroush Mohammadi Samani**  
_MSc Business Analytics, University of Kent_  
[LinkedIn](#) (add your link)

---

> **“If you can’t measure it, you can’t improve it. If you can measure it deeply, you can change the game.”**
