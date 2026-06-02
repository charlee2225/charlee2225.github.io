import numpy as np
from numpy import load
from numpy import save
from keras.models import load_model
import xarray as xr

# load normalization stastistics for denormalization
ERA5_mean_train=load('/ocean/projects/ees230004p/fangwang/generator/model/model_grid_mean_std/data/ERA5_mean_train.npy', mmap_mode='c')
ERA5_std_train=load('/ocean/projects/ees230004p/fangwang/generator/model/model_grid_mean_std/data/ERA5_std_train.npy', mmap_mode='c')

# load predictors data for both train and test
predictors_test=np.load('/data/predictors_test_mean_std_separate.npy', mmap_mode='c')
predictors_train=np.load('/data/predictors_train_mean_std_separate.npy', mmap_mode='c')

# predict both train and test data
predictors=np.concatenate((predictors_train[0*9490:1*9490,:,:,:],predictors_test[0*3650:1*3650,:,:,:]), axis=0)
model = load_model('/save_model/generator_160.h5', compile= False)
predicted=model.predict(predictors)

# reverse the normalization process for train

predicted_train_org=np.ndarray(shape=(9490, 104, 240, 6), dtype= np.float32)
predicted_train_org[:,:,:,0]=predicted[:9490,:,:,0]*ERA5_std_train[:,:,0]+ERA5_mean_train[:,:,0]
predicted_train_org[:,:,:,1]=predicted[:9490,:,:,1]*ERA5_std_train[:,:,1]+ERA5_mean_train[:,:,1]
predicted_train_org[:,:,:,2]=predicted[:9490,:,:,2]*ERA5_std_train[:,:,2]+ERA5_mean_train[:,:,2]
predicted_train_org[:,:,:,3]=predicted[:9490,:,:,3]*ERA5_std_train[:,:,3]+ERA5_mean_train[:,:,3]
predicted_train_org[:,:,:,4]=predicted[:9490,:,:,4]*ERA5_std_train[:,:,4]+ERA5_mean_train[:,:,4]
predicted_train_org[:,:,:,5]=np.exp(predicted[:9490,:,:,5]*ERA5_std_train[:,:,5]+ERA5_mean_train[:,:,5])-1

# reverse the normalization process for test
predicted_test_org=np.ndarray(shape=(3650, 104, 240, 6), dtype= np.float32)
predicted_test_org[:,:,:,0]=predicted[9490:,:,:,0]*ERA5_std_train[:,:,0]+ERA5_mean_train[:,:,0]
predicted_test_org[:,:,:,1]=predicted[9490:,:,:,1]*ERA5_std_train[:,:,1]+ERA5_mean_train[:,:,1]
predicted_test_org[:,:,:,2]=predicted[9490:,:,:,2]*ERA5_std_train[:,:,2]+ERA5_mean_train[:,:,2]
predicted_test_org[:,:,:,3]=predicted[9490:,:,:,3]*ERA5_std_train[:,:,3]+ERA5_mean_train[:,:,3]
predicted_test_org[:,:,:,4]=predicted[9490:,:,:,4]*ERA5_std_train[:,:,4]+ERA5_mean_train[:,:,4]
predicted_test_org[:,:,:,5]=np.exp(predicted[9490:,:,:,5]*ERA5_std_train[:,:,5]+ERA5_mean_train[:,:,5])-1

# save it to netcdf file and repeat it for other GCMs
np.save('/output/MRI-ESM2-0_160.npy')
