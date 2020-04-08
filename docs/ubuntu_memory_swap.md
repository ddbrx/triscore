# https://linuxize.com/post/how-to-add-swap-space-on-ubuntu-18-04/


# Creating a Swap File
---
## Start by creating a file which will be used for swap:
sudo fallocate -l 1G /swapfile

## Only the root user should be able to write and read the swap file. Set the correct permissions by typing:
sudo chmod 600 /swapfile

## Use the mkswap utility to set up a Linux swap area on the file:
sudo mkswap /swapfile

## Activate the swap file using the following command:
sudo swapon /swapfile

## To make the change permanent open the /etc/fstab file
sudo vim /etc/fstab

### and paste the following line:
/swapfile swap swap defaults 0 0

## Verify that the swap is active by using either the swapon or the free command, as shown below:
sudo swapon --show

```
NAME      TYPE  SIZE   USED PRIO
/swapfile file 1024M 507.4M   -1
sudo free -h
              total        used        free      shared  buff/cache   available
Mem:           488M        158M         83M        2.3M        246M        217M
Swap:          1.0G        506M        517M
```


# Adjusting the Swappiness Value
---

Swappiness is a Linux kernel property that defines how often the system will use the swap space. Swappiness can have a value between 0 and 100. A low value will make the kernel to try to avoid swapping whenever possible, while a higher value will make the kernel use the swap space more aggressively.

The default swappiness value is 60. You can check the current swappiness value by typing the following command:

cat /proc/sys/vm/swappiness
60
While the swappiness value of 60 is OK for most Linux systems, for production servers, you may need to set a lower value.
For example, to set the swappiness value to 10, run:

sudo sysctl vm.swappiness=10
To make this parameter persistent across reboots, append the following line to the /etc/sysctl.conf file:

/etc/sysctl.conf
vm.swappiness=10
Copy
The optimal swappiness value depends on your system workload and how the memory is being used. You should adjust this parameter in small increments to find an optimal value.


# Removing a Swap File
---

## Start by deactivating the swap space by typing:
sudo swapoff -v /swapfile

## Next, remove the swap file entry /swapfile swap swap defaults 0 0 from the /etc/fstab file.

## Finally, remove the actual swapfile file using the rm command:
sudo rm /swapfile
