import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import matplotlib

from bayes_race.tracks import ETHZMobil
from bayes_race.models import Dynamic
from bayes_race.params import ORCA
import torch
import yaml
import os
import pickle
from tqdm import tqdm
from deep_dynamics.model.models import string_to_model, string_to_dataset
from deep_dynamics.tools.bayesrace_parser import write_dataset

#####################################################################
# settings

SAVE_RESULTS = False

Ts = 0.02
HORIZON = 15

#####################################################################
# load track

N_SAMPLES = 300
TRACK_NAME = 'ETHZMobil'
track = ETHZMobil(reference='optimal', longer=True)

#####################################################################
# load inputs used to simulate Dynamic model

if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

param_file = "../cfgs/model/deep_dynamics.yaml"
state_dict = "../output/deep_dynamics/16layers_436neurons_2batch_0.000144lr_5horizon_7gru/epoch_385.pth"
dataset_file = "../data/DYN-NMPC-NOCONS-ETHZMobil.npz"
with open(os.path.join(os.path.dirname(state_dict), "scaler.pkl"), "rb") as f:
	ddm_scaler = pickle.load(f)

with open(param_file, 'rb') as f:
	param_dict = yaml.load(f, Loader=yaml.SafeLoader)
ddm = string_to_model[param_dict["MODEL"]["NAME"]](param_dict, eval=True)
ddm.to(device)
ddm.eval()
ddm.load_state_dict(torch.load(state_dict))
features, labels, poses = write_dataset(dataset_file, ddm.horizon, save=False)
stop_idx = len(poses)
for i in range(len(poses)): ## Odometry set to 0 when lap is finished
	if poses[i,0] == 0.0 and poses[i,1] == 0.0:
		stop_idx = i
		break
samples = list(range(50, 275, 25))
driving_inputs = features[:,0,3:5] + features[:,0,5:7]
ddm_dataset = string_to_dataset[param_dict["MODEL"]["NAME"]](features, labels, ddm_scaler)
ddm_predictions = np.zeros((stop_idx - HORIZON, 6, HORIZON+1))
ddm_data_loader = torch.utils.data.DataLoader(ddm_dataset, batch_size=1, shuffle=False)
params = ORCA(control='pwm')
ddm_model = Dynamic(**params)
idt = 0
average_displacement_error = 0.0
final_displacement_error = 0.0
for inputs, labels, norm_inputs in tqdm(ddm_data_loader, total=len(ddm_predictions)):
	if idt == len(ddm_predictions):
		break
	if ddm.is_rnn:
		h = ddm.init_hidden(inputs.shape[0])
		h = h.data
	inputs, labels, norm_inputs = inputs.to(device), labels.to(device), norm_inputs.to(device)
	if ddm.is_rnn:
		_, h, ddm_output = ddm(inputs, norm_inputs, h)
	else:
		_, _, ddm_output = ddm(inputs, norm_inputs)
	# Simulate model
	ddm_output = ddm_output.cpu().detach().numpy()[0]
	idx = 0
	for param in ddm.sys_params:
		params[param] = ddm_output[idx]
		idx += 1
	ddm_model = Dynamic(**params)
	ddm_predictions[idt,:,0] = poses[idt, :]
	displacement_error = 0.0
	for idh in range(HORIZON):
		# Predict over horizon
		ddm_next, _ = ddm_model.sim_continuous(ddm_predictions[idt,:,idh], driving_inputs[idt+idh].reshape(-1,1), [0, Ts], np.zeros((8,1)))
		ddm_predictions[idt,:,idh+1] = ddm_next[:,-1]
		displacement_error += np.sum(np.linalg.norm(ddm_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	average_displacement_error += displacement_error / HORIZON
	final_displacement_error += np.sum(np.linalg.norm(ddm_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	idt += 1
average_displacement_error /= len(ddm_predictions)
final_displacement_error /= len(ddm_predictions)
print("DDM Average Displacement Error:", average_displacement_error)
print("DDM Final Displacement Error:", final_displacement_error)

	
# DPM GT
param_file = "../cfgs/model/deep_pacejka.yaml"
state_dict = "../output/deep_pacejka/2layers_108neurons_16batch_0.002812lr_10horizon_8gru/epoch_385.pth"
with open(os.path.join(os.path.dirname(state_dict), "scaler.pkl"), "rb") as f:
	dpm_scaler = pickle.load(f)
with open(param_file, 'rb') as f:
	param_dict = yaml.load(f, Loader=yaml.SafeLoader)
dpm = string_to_model[param_dict["MODEL"]["NAME"]](param_dict, eval=True)
dpm.cuda()
dpm.load_state_dict(torch.load(state_dict))
features, labels, poses = write_dataset(dataset_file, dpm.horizon, save=False)
dpm_dataset = string_to_dataset[param_dict["MODEL"]["NAME"]](features, labels, dpm_scaler)
dpm_predictions = np.zeros((stop_idx - HORIZON, 6, HORIZON+1))
dpm_data_loader = torch.utils.data.DataLoader(dpm_dataset, batch_size=1, shuffle=False)
params = ORCA(control='pwm')
dpm_model = Dynamic(**params)
idt = 0
average_displacement_error = 0.0
final_displacement_error = 0.0
for inputs, labels, norm_inputs in tqdm(dpm_data_loader, total=len(dpm_predictions)):
	if idt == len(dpm_predictions):
		break
	if dpm.is_rnn:
		h = dpm.init_hidden(inputs.shape[0])
		h = h.data
	inputs, labels, norm_inputs = inputs.to(device), labels.to(device), norm_inputs.to(device)
	if dpm.is_rnn:
		_, h, dpm_output = dpm(inputs, norm_inputs, h)
	else:
		_, _, dpm_output = dpm(inputs, norm_inputs)
	# Simulate model
	dpm_output = dpm_output.cpu().detach().numpy()[0]
	idx = 0
	for param in dpm.sys_params:
		params[param] = dpm_output[idx]
		idx += 1
	dpm_model = Dynamic(**params)
	dpm_predictions[idt,:,0] = poses[idt, :]
	displacement_error = 0.0
	for idh in range(HORIZON):
		# Predict over horizon
		dpm_next, _ = dpm_model.sim_continuous(dpm_predictions[idt,:,idh], driving_inputs[idt+idh].reshape(-1,1), [0, Ts], np.zeros((8,1)))
		dpm_predictions[idt,:,idh+1] = dpm_next[:,-1]
		displacement_error += np.sum(np.linalg.norm(dpm_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	average_displacement_error += displacement_error / HORIZON
	final_displacement_error += np.sum(np.linalg.norm(dpm_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	idt += 1
average_displacement_error /= len(ddm_predictions)
final_displacement_error /= len(ddm_predictions)
print("DPM GT Average Displacement Error:", average_displacement_error)
print("DPM GT Final Displacement Error:", final_displacement_error)

# DPM Iz + 20%
param_file = "../cfgs/model/deep_pacejka.yaml"
state_dict = "../output/deep_pacejka/plus20/epoch_344.pth"
with open(os.path.join(os.path.dirname(state_dict), "scaler.pkl"), "rb") as f:
	dpm_scaler = pickle.load(f)
with open(param_file, 'rb') as f:
	param_dict = yaml.load(f, Loader=yaml.SafeLoader)
param_dict["VEHICLE_SPECS"]["Iz"] *= 1.2
dpm = string_to_model[param_dict["MODEL"]["NAME"]](param_dict, eval=True)
dpm.cuda()
dpm.load_state_dict(torch.load(state_dict))
features, labels, poses = write_dataset(dataset_file, dpm.horizon, save=False)
dpm_dataset = string_to_dataset[param_dict["MODEL"]["NAME"]](features, labels, dpm_scaler)
dpm_plus_predictions = np.zeros((stop_idx - HORIZON, 6, HORIZON+1))
dpm_data_loader = torch.utils.data.DataLoader(dpm_dataset, batch_size=1, shuffle=False)
params = ORCA(control='pwm')
params["Iz"] *= 1.2
dpm_model = Dynamic(**params)
idt = 0
average_displacement_error = 0.0
final_displacement_error = 0.0
for inputs, labels, norm_inputs in tqdm(dpm_data_loader, total=len(dpm_plus_predictions)):
	if idt == len(dpm_plus_predictions):
		break
	if dpm.is_rnn:
		h = dpm.init_hidden(inputs.shape[0])
		h = h.data
	inputs, labels, norm_inputs = inputs.to(device), labels.to(device), norm_inputs.to(device)
	if dpm.is_rnn:
		_, h, dpm_output = dpm(inputs, norm_inputs, h)
	else:
		_, _, dpm_output = dpm(inputs, norm_inputs)
	# Simulate model
	dpm_output = dpm_output.cpu().detach().numpy()[0]
	idx = 0
	for param in dpm.sys_params:
		params[param] = dpm_output[idx]
		idx += 1
	dpm_model = Dynamic(**params)
	dpm_plus_predictions[idt,:,0] = poses[idt, :]
	displacement_error = 0.0
	for idh in range(HORIZON):
		# Predict over horizon
		dpm_next, _ = dpm_model.sim_continuous(dpm_plus_predictions[idt,:,idh], driving_inputs[idt+idh].reshape(-1,1), [0, Ts], np.zeros((8,1)))
		dpm_plus_predictions[idt,:,idh+1] = dpm_next[:,-1]
		displacement_error += np.sum(np.linalg.norm(dpm_plus_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	average_displacement_error += displacement_error / HORIZON
	final_displacement_error += np.sum(np.linalg.norm(dpm_plus_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	idt += 1
average_displacement_error /= len(ddm_predictions)
final_displacement_error /= len(ddm_predictions)
print("DPM +20 Average Displacement Error:", average_displacement_error)
print("DPM +20 Final Displacement Error:", final_displacement_error)

# DPM Iz - 20%
param_file = "../cfgs/model/deep_pacejka.yaml"
state_dict = "../output/deep_pacejka/minus20/epoch_364.pth"
param_dict["VEHICLE_SPECS"]["Iz"] *= 0.8
with open(os.path.join(os.path.dirname(state_dict), "scaler.pkl"), "rb") as f:
	dpm_scaler = pickle.load(f)
with open(param_file, 'rb') as f:
	param_dict = yaml.load(f, Loader=yaml.SafeLoader)
dpm = string_to_model[param_dict["MODEL"]["NAME"]](param_dict, eval=True)
dpm.cuda()
dpm.load_state_dict(torch.load(state_dict))
features, labels, poses = write_dataset(dataset_file, dpm.horizon, save=False)
dpm_dataset = string_to_dataset[param_dict["MODEL"]["NAME"]](features, labels, dpm_scaler)
dpm_minus_predictions = np.zeros((stop_idx - HORIZON, 6, HORIZON+1))
dpm_data_loader = torch.utils.data.DataLoader(dpm_dataset, batch_size=1, shuffle=False)
params = ORCA(control='pwm')
params["Iz"] *= 0.8
dpm_model = Dynamic(**params)
idt = 0
average_displacement_error = 0.0
final_displacement_error = 0.0
for inputs, labels, norm_inputs in tqdm(dpm_data_loader, total=len(dpm_minus_predictions)):
	if idt == len(dpm_minus_predictions):
		break
	if dpm.is_rnn:
		h = dpm.init_hidden(inputs.shape[0])
		h = h.data
	inputs, labels, norm_inputs = inputs.to(device), labels.to(device), norm_inputs.to(device)
	if dpm.is_rnn:
		_, h, dpm_output = dpm(inputs, norm_inputs, h)
	else:
		_, _, dpm_output = dpm(inputs, norm_inputs)
	# Simulate model
	dpm_output = dpm_output.cpu().detach().numpy()[0]
	idx = 0
	for param in dpm.sys_params:
		params[param] = dpm_output[idx]
		idx += 1
	dpm_model = Dynamic(**params)
	dpm_minus_predictions[idt,:,0] = poses[idt, :]
	displacement_error = 0.0
	for idh in range(HORIZON):
		# Predict over horizon
		dpm_next, _ = dpm_model.sim_continuous(dpm_minus_predictions[idt,:,idh], driving_inputs[idt+idh].reshape(-1,1), [0, Ts], np.zeros((8,1)))
		dpm_minus_predictions[idt,:,idh+1] = dpm_next[:,-1]
		displacement_error += np.sum(np.linalg.norm(dpm_minus_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	average_displacement_error += displacement_error / HORIZON
	final_displacement_error += np.sum(np.linalg.norm(dpm_minus_predictions[idt,:2,idh+1] - poses[idt+idh+1,:2]))
	idt += 1
average_displacement_error /= len(ddm_predictions)
final_displacement_error /= len(ddm_predictions)
print("DPM -20 Average Displacement Error:", average_displacement_error)
print("DPM -20 Final Displacement Error:", final_displacement_error)

#####################################################################
# plots
font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 22}
matplotlib.rc('font', **font)
plt.figure(figsize=(12,8))
plt.axis('equal')
plt.plot(track.x_outer, track.y_outer, 'k', lw=0.5, alpha=0.5)
plt.plot(track.x_inner, track.y_inner, 'k', lw=0.5, alpha=0.5)
plt.plot(poses[:260,0], poses[:260,1], 'b', lw=1)
legend_initialized = False
for idx in samples:
	if not legend_initialized:
		plt.plot(poses[idx:idx+HORIZON,0], poses[idx:idx+HORIZON,1], '--bo', label='Ground Truth')
		plt.plot(ddm_predictions[idx, 0, :], ddm_predictions[idx, 1, :], '--go', label="Deep Dynamics")
		plt.plot(dpm_predictions[idx, 0, :], dpm_predictions[idx, 1, :], '--ro', label="Deep Pacejka (GT)")
		plt.plot(dpm_plus_predictions[idx, 0, :], dpm_plus_predictions[idx, 1, :], '--co', label="Deep Pacejka (+20%)")
		plt.plot(dpm_minus_predictions[idx, 0, :], dpm_minus_predictions[idx, 1, :], '--mo', label="Deep Pacejka (-20%)")
		plt.plot(poses[idx,0], poses[idx,1], 'bo')
		plt.text(poses[idx,0]-0.05, poses[idx,1]+0.05, "%.1f" % float(idx*Ts), color='b', fontsize=18, ha='right', va='top')
		legend_initialized = True
	else:
		plt.plot(poses[idx:idx+HORIZON,0], poses[idx:idx+HORIZON,1], '--bo')
		plt.plot(ddm_predictions[idx, 0, :], ddm_predictions[idx, 1, :], '--go')
		plt.plot(dpm_predictions[idx, 0, :], dpm_predictions[idx, 1, :], '--ro')
		plt.plot(dpm_plus_predictions[idx, 0, :], dpm_plus_predictions[idx, 1, :], '--co')
		plt.plot(dpm_minus_predictions[idx, 0, :], dpm_minus_predictions[idx, 1, :], '--mo')
		plt.plot(poses[idx,0], poses[idx,1], 'bo')
		plt.text(poses[idx,0]-0.05, poses[idx,1]+0.05, "%.1f" % float(idx*Ts), color='b', fontsize=18, ha='right', va='top')

plt.legend(loc='upper center', ncol=3, bbox_to_anchor=(0.5,1.15), frameon=False)
plt.show()