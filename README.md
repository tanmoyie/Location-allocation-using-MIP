## Location Allocation using Mixed Integer Programming (MIP)

# Summary
**Situation**: Develop a Mixed Integer Programming (MIP) optimization model for an oil spill problem to help strategic decision-making.
**Task**: How many and where to build oil spill response stations in Canadian Arctic? Will additional response stations improve coverage?
**Action**: Build optimization model to find optimal facility location and allocation. This Optimization Model Maximize spill coverage while ensuring minimum response time, and sensitive areas are covered.
**Result**: 95% spill coverage; Build 5 response stations

![P-III abstract](https://github.com/tanmoyie/Location-allocation-using-MIP/assets/19787712/2e6b3437-881d-437c-90a7-df399719f715)


# Comments
1.	main.py file can be carefully run to obtain related outputs
2.	requirement.txt file contains all Python packages needed for this project 
3.	The main optimization engine is written in model_PAMIP.py file
4.	Source code of Figure 1, 2 & 3 can be found in data_visualization.py file
5.	data_generation.py file is currently empty. This file is for next version of the model! 
6.	Some custom functions are written in custom_functions.py to avoid duplicates in the main.py file

# Reference
Tanmoy Das, Floris Goerlandt, Ronald Pelot (2023). A Mixed Integer Programming Approach to Improve Oil Spill Response Resource Allocation in the Canadian Arctic. Multimodal Transportation, 3(1). https://doi.org/10.1016/j.multra.2023.100110
