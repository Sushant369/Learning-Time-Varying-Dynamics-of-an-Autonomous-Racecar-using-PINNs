import numpy as np

# Load the .npz file
data = np.load('C:\\Users\\susha\\Documents\\Sci-ML-Project\\deep-dynamics\\deep_dynamics\\data\\LVMS_23_01_04_A_16.npz')

# data is now a NpzFile object acting like a dictionary
# You can list all the files/items contained in this .npz file
print("Keys in the npz file:", list(data.keys()))

print(data["labels"])

# Access individual arrays with the keys, for example:
# array_example = data['arr_0']  # Replace 'arr_0' with the actual key name

# Optionally, if you know the names of the arrays, you can use them directly
# For example, if you know there is an array saved under the key 'features'
# features_array = data['features']

# Don't forget to close the file when you're done
data.close()
