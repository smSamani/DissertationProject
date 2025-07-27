# Project Progress Summary – Feature Engineering

## Data Selection & Scope

We selected the open-access StatsBomb dataset as our primary data source, focusing specifically on Bayer Leverkusen’s full season in the Bundesliga. This dataset provides highly detailed event logs (event.json), lineup information (lineup.json), and 360-degree freeze-frame data (360.json) for each match. To ensure future flexibility and easy access, we organized the data so that each match has its own folder containing all three files.

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

In the third phase, we used StatsBomb’s freeze-frame data to extract spatial context features at the moment of each shot. These include:

- **Number of Opponents in Front:** Counts the defenders directly in front of the shooter—specifically, opponents whose x-coordinate is greater than the shooter’s (closer to goal) and whose y-coordinate is within ±10% of the shooter’s y (roughly in line horizontally).
- **Distance to Goal Center:** The straight-line (Euclidean) distance from the shooter to the center of the goal.
- **Shot Angle:** The size of the open angle to the goal, calculated using the shooter’s position and the goalposts.
- **Match Period:** Whether the shot occurred in the first or second half.
- **Absolute Minute:** The actual minute of the match in which the shot happened (e.g., 54th minute).

These features help quantify the difficulty and quality of the shooting opportunity, providing important context for xG prediction.