import matplotlib.pyplot as plt

# Epoch values
epochs = list(range(1,401))




# Initialize empty lists to store data
index = []
DDM_training_loss = []
DDM_validation_loss = []
DGDM_training_loss = []
DGDM_validation_loss = []

# Read the data from the text file
file_path = "C:\\Users\\susha\\Documents\\Sci-ML-Project\\deep-dynamics\\Round2\\deep-dynamics\\deep_dynamics\\model\\loss_store_tune_DDM.txt"
with open(file_path, 'r') as file:
    for line in file:
        # Split each line into components
        data = line.split()
        # Add the components to the respective lists
        DDM_training_loss.append(float(data[1]))
        DDM_validation_loss.append(float(data[2]))

file_path = "C:\\Users\\susha\\Documents\\Sci-ML-Project\\deep-dynamics\\Round2\\deep-dynamics\\deep_dynamics\\model\\loss_store_tune_DGDM.txt"
with open(file_path, 'r') as file:
    for line in file:
        # Split each line into components
        data = line.split()
        # Add the components to the respective lists
        DGDM_training_loss.append(float(data[1]))
        DGDM_validation_loss.append(float(data[2]))



# # Plot model 1 training and validation losses 
plt.plot(epochs, DDM_training_loss, label=' DDM Training Loss', color='blue')
plt.plot(epochs, DGDM_training_loss, label='DGDM Training Loss', color='cyan')

# Plot model 2 training and validation losses
plt.plot(epochs, DDM_validation_loss, label='DDM Validation Loss', color='red')
plt.plot(epochs, DGDM_validation_loss, label='DGDM Validation Loss', color='orange')

# Adding labels, title, and legend
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Model Training and Validation Loss Comparison')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()
