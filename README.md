# Project Name: Learning-Time-Varying-Dynamics-of-an-Autonomous-Racecar-using-PINNs

### Course: ECEN 689 - Scientific Machine Learning
### Instructor: Dr. Ulisses Braga-Neto
### University Name: Texas A&M University, College Station

### Repository Maintained by:
- Sushant Vijay Shelar (UIN: 733001479)
- Mohini Priya Kolluri (UIN: 734004070)


## Introduction 
Deep Dynamics is a physics-informed neural network (PINN) designed to model the complex dynamics observed in a high-speed, competitive racing environment. Using a historical horizon of the vehicle's state and control inputs, Deep Dynamics learns to produce accurate coefficient estimates for a dynamic single-track model that best describes the vehicle's motion. Specifically, this includes Pacejka Magic Formula coefficients for the front and rear wheels, coefficients for a linear drivetrain model, and the vehicle's moment of inertia. The Physics Guard layer ensures that estimated coefficients always lie within their physically-meaningful range, determined by the meaning behind each coefficient.

## Installation

It is recommended to create a new conda environment:

```
conda create --name deep_dynamics python=3.10
conda activate deep_dynamics
```

To install Deep Dynamics:

```
git clone git@github.com:linklab-uva/deep-dynamics.git
cd deep-dynamics/
pip install -e .
```

## Processing Data

Data collected from the [Bayesrace vehicle dynamics simulator](https://github.com/jainachin/bayesrace) and the AV-21 full-scale autonomous racecar competing in the [Indy Autonomous Challenge](https://www.indyautonomouschallenge.com/) run by the [Cavalier Autonomous Racing Team](https://autonomousracing.dev/) is provided for training and testing.

Bayesrace:
```
1. deep_dynamics/data/DYN-PP-ETHZ.npz
2. deep_dynamics/data/DYN-PP-ETHZMobil.npz
```

Indy Autonomous Challenge (IAC):
```
1. deep_dynamics/data/LVMS_23_01_04_A.csv
2. deep_dynamics/data/LVMS_23_01_04_B.csv
3. deep_dynamics/data/Putnam_park2023_run2_1.csv
4. deep_dynamics/data/Putnam_park2023_run4_1.csv
5. deep_dynamics/data/Putnam_park2023_run4_2.csv
```

To convert data from Bayesrace to the format needed for training:

```
cd tools/
./bayesrace_parser.py {path to dataset} {historical horizon size}
```

Historical horizon size refers to the number of historical state and control input pairs used as features during training. The process is similar for IAC data:

```
cd tools/
./csv_parser.py {path to dataset} {historical horizon size}
```

The resulting file will be stored under `{path to dataset}_{historical_horizon_size}.npz`.

## Model Configuration

Configurations for Deep Dynamics and the closely related [Deep Pacejka Model](https://arxiv.org/pdf/2207.07920.pdf) are provided under `deep_dynamics/cfgs/`. The items listed under `PARAMETERS` are the variables estimated by each model. The ground-truth coefficient values used for the Bayesrace simulator are displayed next to each coefficient (i.e. `Bf: 5.579` indicates the coefficient Bf was set to 5.579). The ground-truth values are only used for evaluation purposes, they are not accessible to the models during training. The Physics Guard layer requires ranges for the coefficients estimated by Deep Dynamics and can be specified with the `Min` and `Max` arguments.

Certain properties for the vehicle are required for training. Provided under `VEHICLE_SPECS`, this includes the vehicle's mass and the distance from the vehicle's center of gravity (COG) to the front and rear axles (`lf` and `lr`). The Deep Pacejka Model also requires the vehicle's moment of inertia (`Iz`) is specified.

Under `MODEL`, the layers for each model can be specified. The `HORIZON` refers to the historical horizon of state and control inputs used as features. Under `LAYERS`, the input and hidden layers of the model can be specified. Lastly, the optimization parameters are provided under `OPTIMIZATION`.

## Model Training

To run an individual training experiment, use:

```
cd deep_dynamics/model/
python3 train.py {path to cfg} {path to dataset} {name of experiment}
```

The optional flag `--log_wandb` can also be added to track results using the [Weights & Biases Platform](https://wandb.ai/site). Model weights will be stored under `../output/{name of experiment}` whenever the validation loss decreases below the previous minima.

To run multiple trials in parallel for hyperparameter tuning, use:

```
cd deep_dynamics/model/
python3 tune_hyperparameters.py {path to cfg}
```

The desired dataset must be manually specified within `tune_hyperparameters.py` as well as the ranges for the hyperparameter tuning experiment. Trials are run using the [RayTune scheduler](https://docs.ray.io/en/latest/tune/index.html).

## Model Evaluation

To evaluate an individual model, use:

```
cd deep_dynamics/model/
python3 evaluate.py {path to cfg} {path to dataset} {path to model weights}
```

This will evaluate the model's RMSE and maximum error for the predicted state variables across the specified dataset. Additionally, the optional flag `--eval_coeffs` can be used to compare the mean and standard deviation of the model's internally estimated coefficients.

To evaluate multiple trials from hyperparameter tuning, use:

```
cd deep_dynamics/model/
python3 test_hyperparameters.py {path to cfg}
```



## Acknowledgments

This project utilizes concepts and methodologies from the following research work:

- **Deep Dynamics: Vehicle Dynamics Modeling with a Physics-Informed Neural Network for Autonomous Racing** by John Chrosniak, Jingyun Ning, and Madhur Behl (2023). This foundational research significantly influenced the development of our model's architecture and capabilities. The detailed citation for their work is provided below:

@misc{chrosniak2023deep,
title={Deep Dynamics: Vehicle Dynamics Modeling with a Physics-Informed Neural Network for Autonomous Racing},
author={John Chrosniak and Jingyun Ning and Madhur Behl},
year={2023},
eprint={2312.04374},
archivePrefix={arXiv},
primaryClass={cs.RO}
}


## References
- **Deep Dynamics Model**: Developed by the LINK Lab at the University of Virginia. The codebase provided insights and foundational code for our dynamics modeling component. [View the repository](https://github.com/linklab-uva/deep-dynamics/tree/main).

- **Ph.D. Thesis on Deep Learning Dynamics**: This thesis from the University of Virginia's digital repository influenced our theoretical approach to machine learning model architecture. [Access the thesis](https://libraetd.lib.virginia.edu/public_view/qr46r2095).

- **Research Paper on Dynamics Prediction**: This paper provided crucial background and validation of the concepts we've implemented in our project. [Read the paper](https://arxiv.org/pdf/2312.04374v1).
