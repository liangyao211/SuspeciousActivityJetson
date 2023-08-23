from tower_security import TowerSecurity
import cv2
import matplotlib.pyplot as plt
import numpy as np


security=TowerSecurity()
security.update_fence_mask('dump_dir/test_images/output_0002.jpg')
print(np.sum(security.mask))
plt.imshow(security.mask)
plt.show()

