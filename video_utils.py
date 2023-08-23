import os
from io import BytesIO
import cv2
import random
import string
import glob
import subprocess
### Need apt-get install -y ffmpeg (apt-get update also)
### 
class m4v_reader:
	def __init__(self, filename, proc_fps=2):
		self.proc_fps=proc_fps
		
		### Check if the folder exists with the images..!
		self.temp_dir=filename[:-4]
		self.image_stored=False
		print(f'folder name is {self.temp_dir}')

		if os.path.isdir(self.temp_dir):
			self.image_stored=True
			self.files=glob.glob(self.temp_dir+'/*.jpg')
			self.files.sort()
		else:
			dir_name=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
			self.temp_dir=f'/tmp/{dir_name}/'
			print('tmp dir is', self.temp_dir)
			os.mkdir(f'{self.temp_dir}')
			os.system(f'ls -la {self.temp_dir}')

			self.vid=cv2.VideoCapture(filename)
			n_frames=int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))
			fps = self.vid.get(cv2.CAP_PROP_FPS)
			skip=round(n_frames/(proc_fps*fps))
			print(f'fps:{fps} nf:{n_frames}, skip:{skip}')
			self.frame_ids=range(0,n_frames,skip)
			print(self.frame_ids)
			self.files=[f'{self.temp_dir}/output_{fidx}.jpg' for fidx in range(len(self.frame_ids))]
		
		
	def read(self,idx):
		filename= self.files[idx]
		if not self.image_stored:
			self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.frame_ids[idx])
			res, frame = self.vid.read()
			cv2.imwrite(filename,frame)
			#print('{self.temp_dir}/output_{idx}.jpg',frame.shape, res)
		return filename

	def destroy(self):
		os.system(f'rm -rf {self.temp_dir}')

			
	
class Video2Frame:
	def __init__(self, filename, proc_fps=2):
		self.proc_fps=proc_fps
		self.fps=60
		self.nframes = 0
		
		dir_name=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
		self.temp_dir=f'/tmp/{dir_name}/'
		print('tmp dir is', self.temp_dir)
		os.system(f'mkdir {self.temp_dir}')
		#os.system(f'ffmpeg -hide_banner -loglevel error -i {filename} -r 0.5 {self.temp_dir}/output_%04d.jpg')
		cmd='ffmpeg -hide_banner -loglevel error -i {filename} -r 0.5 {self.temp_dir}/output_%04d.jpg'
		result = subprocess.run([cmd], shell=True)
		print(f'ffmpeg status is {result.stdout}')                
		self.files=glob.glob(self.temp_dir+'*.jpg')
		print(f'{len(self.files)} frames extracted from {filename}')
		
	def read(self,idx):
		return self.files[idx]
		#return image
		
	def get(self,prop):
		if prop==cv2.CAP_PROP_FPS:
			return self.fps
		elif prop==CAP_PROP_FRAME_COUNT:
			return self.nframes
		else:
			raise "Property is not defined"
	
	def destroy(self):
		os.system(f'rm -rf {self.temp_dir}')
