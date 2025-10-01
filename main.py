vou copiar o código o voce pode checar o que está faltando


Last login: Tue Sep 30 20:39:05 on ttys000
alessandra@192 ~ % ssh pi@pi.local
Linux pi 6.12.47+rpt-rpi-2712 #1 SMP PREEMPT Debian 1:6.12.47-1+rpt1~bookworm (2025-09-16) aarch64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Sep 30 20:39:12 2025 from 2804:14c:3d6:8333:5003:af01:5c7a:7741
pi@pi:~ $ scp -r pi_productivity pi@<ip_do_pi>:~
-bash: ip_do_pi: No such file or directory
pi@pi:~ $ scp -r pi_productivity pi@pi.local:~
The authenticity of host 'pi.local (192.168.0.9)' can't be established.
ED25519 key fingerprint is SHA256:IQYZvwvJtVJVsni+Ww8UoHKZ8cCc6YomY8JF5Gq9KpI.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'pi.local' (ED25519) to the list of known hosts.
pi@pi.local: Permission denied (publickey).
scp: Connection closed
pi@pi:~ $ scp -r pi_productivity pi@pi.local:~
pi@pi.local: Permission denied (publickey).
scp: Connection closed
pi@pi:~ $ hostname -I
192.168.0.9 2804:14c:3d6:8333:dc46:567a:8a60:9861 
pi@pi:~ $ cd ~/pi_productivity
pi@pi:~/pi_productivity $ source ~/.venv/bin/activate
(.venv) pi@pi:~/pi_productivity $ pip install -r requirements.txt
Looking in indexes: https://pypi.org/simple, https://www.piwheels.org/simple
Collecting python-dotenv==1.0.1
  Downloading https://www.piwheels.org/simple/python-dotenv/python_dotenv-1.0.1-py3-none-any.whl (19 kB)
Collecting requests==2.32.3
  Downloading https://www.piwheels.org/simple/requests/requests-2.32.3-py3-none-any.whl (64 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 64.9/64.9 kB 229.9 kB/s eta 0:00:00
Collecting pillow==10.4.0
  Downloading pillow-10.4.0-cp311-cp311-manylinux_2_28_aarch64.whl (4.4 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.4/4.4 MB 1.4 MB/s eta 0:00:00
Collecting sense-hat==2.6.0
  Downloading https://www.piwheels.org/simple/sense-hat/sense_hat-2.6.0-py3-none-any.whl (18 kB)
Collecting tzdata==2024.1
  Downloading https://www.piwheels.org/simple/tzdata/tzdata-2024.1-py2.py3-none-any.whl (345 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 345.4/345.4 kB 349.3 kB/s eta 0:00:00
Collecting pytz==2024.1
  Downloading https://www.piwheels.org/simple/pytz/pytz-2024.1-py3-none-any.whl (505 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 505.5/505.5 kB 501.9 kB/s eta 0:00:00
Collecting opencv-python==4.10.0.84
  Downloading opencv_python-4.10.0.84-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (41.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 41.7/41.7 MB 2.6 MB/s eta 0:00:00
Collecting pytesseract==0.3.13
  Downloading https://www.piwheels.org/simple/pytesseract/pytesseract-0.3.13-py3-none-any.whl (14 kB)
Collecting charset-normalizer<4,>=2
  Downloading charset_normalizer-3.4.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl (145 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 145.5/145.5 kB 2.1 MB/s eta 0:00:00
Collecting idna<4,>=2.5
  Downloading https://www.piwheels.org/simple/idna/idna-3.10-py3-none-any.whl (70 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 70.4/70.4 kB 281.1 kB/s eta 0:00:00
Collecting urllib3<3,>=1.21.1
  Downloading https://www.piwheels.org/simple/urllib3/urllib3-2.5.0-py3-none-any.whl (129 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 129.8/129.8 kB 545.6 kB/s eta 0:00:00
Collecting certifi>=2017.4.17
  Downloading https://www.piwheels.org/simple/certifi/certifi-2025.8.3-py3-none-any.whl (161 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 161.2/161.2 kB 2.3 MB/s eta 0:00:00
Collecting numpy
  Downloading numpy-2.3.3-cp311-cp311-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl (14.6 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14.6/14.6 MB 1.8 MB/s eta 0:00:00
Collecting packaging>=21.3
  Downloading https://www.piwheels.org/simple/packaging/packaging-25.0-py3-none-any.whl (66 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 66.5/66.5 kB 222.2 kB/s eta 0:00:00
Installing collected packages: pytz, urllib3, tzdata, python-dotenv, pillow, packaging, numpy, idna, charset-normalizer, certifi, sense-hat, requests, pytesseract, opencv-python
Successfully installed certifi-2025.8.3 charset-normalizer-3.4.3 idna-3.10 numpy-2.3.3 opencv-python-4.10.0.84 packaging-25.0 pillow-10.4.0 pytesseract-0.3.13 python-dotenv-1.0.1 pytz-2024.1 requests-2.32.3 sense-hat-2.6.0 tzdata-2024.1 urllib3-2.5.0
(.venv) pi@pi:~/pi_productivity $ cp .env.example .env
cp: cannot stat '.env.example': No such file or directory
(.venv) pi@pi:~/pi_productivity $ cd ~/pi_productivity
nano .env
(.venv) pi@pi:~/pi_productivity $ cd ~/pi_productivity
mv .env.exemplo .env
nano .env
mv: cannot stat '.env.exemplo': No such file or directory
(.venv) pi@pi:~/pi_productivity $ rm -f .env.exemple
(.venv) pi@pi:~/pi_productivity $ sudo apt update
sudo apt install -y python3-picamera2 tesseract-ocr sense-hat
Hit:1 http://deb.debian.org/debian bookworm InRelease
Hit:2 http://deb.debian.org/debian-security bookworm-security InRelease
Hit:3 http://deb.debian.org/debian bookworm-updates InRelease
Hit:4 http://archive.raspberrypi.com/debian bookworm InRelease   
Reading package lists... Done                                    
Building dependency tree... Done
Reading state information... Done
5 packages can be upgraded. Run 'apt list --upgradable' to see them.
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
python3-picamera2 is already the newest version (0.3.31-1).
sense-hat is already the newest version (1.5).
The following packages were automatically installed and are no longer required:
  libbasicusageenvironment1 libgroupsock8 liblivemedia77 python3-v4l2
Use 'sudo apt autoremove' to remove them.
The following additional packages will be installed:
  liblept5 libtesseract5 tesseract-ocr-eng tesseract-ocr-osd
The following NEW packages will be installed:
  liblept5 libtesseract5 tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd
0 upgraded, 5 newly installed, 0 to remove and 5 not upgraded.
Need to get 7,044 kB of archives.
After this operation, 23.8 MB of additional disk space will be used.
Get:1 http://deb.debian.org/debian bookworm/main arm64 liblept5 arm64 1.82.0-3+b3 [973 kB]
Get:2 http://deb.debian.org/debian bookworm/main arm64 libtesseract5 arm64 5.3.0-2 [1,123 kB]
Get:3 http://deb.debian.org/debian bookworm/main arm64 tesseract-ocr-eng all 1:4.1.0-2 [1,594 kB]
Get:4 http://deb.debian.org/debian bookworm/main arm64 tesseract-ocr-osd all 1:4.1.0-2 [2,992 kB]
Get:5 http://deb.debian.org/debian bookworm/main arm64 tesseract-ocr arm64 5.3.0-2 [363 kB]
Fetched 7,044 kB in 3s (2,526 kB/s)     
Selecting previously unselected package liblept5:arm64.
(Reading database ... 150679 files and directories currently installed.)
Preparing to unpack .../liblept5_1.82.0-3+b3_arm64.deb ...
Unpacking liblept5:arm64 (1.82.0-3+b3) ...
Selecting previously unselected package libtesseract5:arm64.
Preparing to unpack .../libtesseract5_5.3.0-2_arm64.deb ...
Unpacking libtesseract5:arm64 (5.3.0-2) ...
Selecting previously unselected package tesseract-ocr-eng.
Preparing to unpack .../tesseract-ocr-eng_1%3a4.1.0-2_all.deb ...
Unpacking tesseract-ocr-eng (1:4.1.0-2) ...
Selecting previously unselected package tesseract-ocr-osd.
Preparing to unpack .../tesseract-ocr-osd_1%3a4.1.0-2_all.deb ...
Unpacking tesseract-ocr-osd (1:4.1.0-2) ...
Selecting previously unselected package tesseract-ocr.
Preparing to unpack .../tesseract-ocr_5.3.0-2_arm64.deb ...
Unpacking tesseract-ocr (5.3.0-2) ...
Setting up tesseract-ocr-eng (1:4.1.0-2) ...
Setting up liblept5:arm64 (1.82.0-3+b3) ...
Setting up libtesseract5:arm64 (5.3.0-2) ...
Setting up tesseract-ocr-osd (1:4.1.0-2) ...
Setting up tesseract-ocr (5.3.0-2) ...
Processing triggers for man-db (2.11.2-2) ...
Processing triggers for libc-bin (2.36-9+rpt2+deb12u12) ...
(.venv) pi@pi:~/pi_productivity $ cd ~/pi_productivity
ls -1
camera_posture.py
env.example
epaper_display.py
main.py
motion_client.py
ocr_notes.py
README.md
requirements.txt
sense_modes.py
utils.py
(.venv) pi@pi:~/pi_productivity $ cd ~/pi_productivity
mv env.example .env
nano .env
(.venv) pi@pi:~/pi_productivity $ cd
(.venv) pi@pi:~ $ cd
(.venv) pi@pi:~ $ xit
-bash: xit: command not found
(.venv) pi@pi:~ $ exit
logout
Connection to pi.local closed.
alessandra@192 ~ % ssh pi@pi.local
Linux pi 6.12.47+rpt-rpi-2712 #1 SMP PREEMPT Debian 1:6.12.47-1+rpt1~bookworm (2025-09-16) aarch64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Sep 30 20:45:59 2025 from 2804:14c:3d6:8333:5003:af01:5c7a:7741
pi@pi:~ $ sudo apt update
sudo apt install -y python3-picamera2 tesseract-ocr sense-hat
Hit:1 http://deb.debian.org/debian bookworm InRelease
Hit:2 http://deb.debian.org/debian-security bookworm-security InRelease
Hit:3 http://deb.debian.org/debian bookworm-updates InRelease
Hit:4 http://archive.raspberrypi.com/debian bookworm InRelease
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
5 packages can be upgraded. Run 'apt list --upgradable' to see them.
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
python3-picamera2 is already the newest version (0.3.31-1).
tesseract-ocr is already the newest version (5.3.0-2).
sense-hat is already the newest version (1.5).
The following packages were automatically installed and are no longer required:
  libbasicusageenvironment1 libgroupsock8 liblivemedia77 python3-v4l2
Use 'sudo apt autoremove' to remove them.
0 upgraded, 0 newly installed, 0 to remove and 5 not upgraded.
pi@pi:~ $ pip install -r requirements.txt
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
    
    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
    sure you have python3-full installed.
    
    For more information visit http://rptl.io/venv

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
pi@pi:~ $ cd ~/pi_productivity
pi@pi:~/pi_productivity $ python3 -m venv .venv
source .venv/bin/activate
(.venv) pi@pi:~/pi_productivity $ pip install -r requirements.txt
Looking in indexes: https://pypi.org/simple, https://www.piwheels.org/simple
Collecting python-dotenv==1.0.1
  Using cached https://www.piwheels.org/simple/python-dotenv/python_dotenv-1.0.1-py3-none-any.whl (19 kB)
Collecting requests==2.32.3
  Using cached https://www.piwheels.org/simple/requests/requests-2.32.3-py3-none-any.whl (64 kB)
Collecting pillow==10.4.0
  Using cached pillow-10.4.0-cp311-cp311-manylinux_2_28_aarch64.whl (4.4 MB)
Collecting sense-hat==2.6.0
  Using cached https://www.piwheels.org/simple/sense-hat/sense_hat-2.6.0-py3-none-any.whl (18 kB)
Collecting tzdata==2024.1
  Using cached https://www.piwheels.org/simple/tzdata/tzdata-2024.1-py2.py3-none-any.whl (345 kB)
Collecting pytz==2024.1
  Using cached https://www.piwheels.org/simple/pytz/pytz-2024.1-py3-none-any.whl (505 kB)
Collecting opencv-python==4.10.0.84
  Using cached opencv_python-4.10.0.84-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (41.7 MB)
Collecting pytesseract==0.3.13
  Using cached https://www.piwheels.org/simple/pytesseract/pytesseract-0.3.13-py3-none-any.whl (14 kB)
Collecting charset-normalizer<4,>=2
  Using cached charset_normalizer-3.4.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl (145 kB)
Collecting idna<4,>=2.5
  Using cached https://www.piwheels.org/simple/idna/idna-3.10-py3-none-any.whl (70 kB)
Collecting urllib3<3,>=1.21.1
  Using cached https://www.piwheels.org/simple/urllib3/urllib3-2.5.0-py3-none-any.whl (129 kB)
Collecting certifi>=2017.4.17
  Using cached https://www.piwheels.org/simple/certifi/certifi-2025.8.3-py3-none-any.whl (161 kB)
Collecting numpy
  Using cached numpy-2.3.3-cp311-cp311-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl (14.6 MB)
Collecting packaging>=21.3
  Using cached https://www.piwheels.org/simple/packaging/packaging-25.0-py3-none-any.whl (66 kB)
Installing collected packages: pytz, urllib3, tzdata, python-dotenv, pillow, packaging, numpy, idna, charset-normalizer, certifi, sense-hat, requests, pytesseract, opencv-python
Successfully installed certifi-2025.8.3 charset-normalizer-3.4.3 idna-3.10 numpy-2.3.3 opencv-python-4.10.0.84 packaging-25.0 pillow-10.4.0 pytesseract-0.3.13 python-dotenv-1.0.1 pytz-2024.1 requests-2.32.3 sense-hat-2.6.0 tzdata-2024.1 urllib3-2.5.0
(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 6, in <module>
    from sense_modes import HapvidaMode, CarePlusMode, StudyADHDMode, LeisureMode, sense
  File "/home/pi/pi_productivity/sense_modes.py", line 3, in <module>
    from sense_hat import SenseHat
  File "/home/pi/pi_productivity/.venv/lib/python3.11/site-packages/sense_hat/__init__.py", line 2, in <module>
    from .sense_hat import SenseHat, SenseHat as AstroPi
  File "/home/pi/pi_productivity/.venv/lib/python3.11/site-packages/sense_hat/sense_hat.py", line 11, in <module>
    import RTIMU  # custom version
    ^^^^^^^^^^^^
ModuleNotFoundError: No module named 'RTIMU'
(.venv) pi@pi:~/pi_productivity $ deactivate
pi@pi:~/pi_productivity $ ls -la
total 68
drwxr-xr-x  4 pi pi 4096 Sep 30 21:10 .
drwx------ 17 pi pi 4096 Sep 30 20:50 ..
-rw-r--r--  1 pi pi 2134 Sep 30 20:50 camera_posture.py
-rw-r--r--  1 pi pi  184 Sep 30 21:06 .env
-rw-r--r--  1 pi pi  155 Sep 30 20:57 .env.example
-rw-r--r--  1 pi pi 2366 Sep 30 20:50 epaper_display.py
-rw-r--r--  1 pi pi 5745 Sep 30 20:50 main.py
-rw-r--r--  1 pi pi 3866 Sep 30 20:50 motion_client.py
-rw-r--r--  1 pi pi 1299 Sep 30 20:50 ocr_notes.py
drwxr-xr-x  2 pi pi 4096 Sep 30 21:10 __pycache__
-rw-r--r--  1 pi pi  816 Sep 30 20:50 README.md
-rw-r--r--  1 pi pi  144 Sep 30 20:50 requirements.txt
-rw-r--r--  1 pi pi 4963 Sep 30 20:50 sense_modes.py
-rw-r--r--  1 pi pi  631 Sep 30 20:50 utils.py
drwxr-xr-x  5 pi pi 4096 Sep 30 21:09 .venv
pi@pi:~/pi_productivity $ rm -f env.example
pi@pi:~/pi_productivity $ ls -la
total 68
drwxr-xr-x  4 pi pi 4096 Sep 30 21:10 .
drwx------ 17 pi pi 4096 Sep 30 20:50 ..
-rw-r--r--  1 pi pi 2134 Sep 30 20:50 camera_posture.py
-rw-r--r--  1 pi pi  184 Sep 30 21:06 .env
-rw-r--r--  1 pi pi  155 Sep 30 20:57 .env.example
-rw-r--r--  1 pi pi 2366 Sep 30 20:50 epaper_display.py
-rw-r--r--  1 pi pi 5745 Sep 30 20:50 main.py
-rw-r--r--  1 pi pi 3866 Sep 30 20:50 motion_client.py
-rw-r--r--  1 pi pi 1299 Sep 30 20:50 ocr_notes.py
drwxr-xr-x  2 pi pi 4096 Sep 30 21:10 __pycache__
-rw-r--r--  1 pi pi  816 Sep 30 20:50 README.md
-rw-r--r--  1 pi pi  144 Sep 30 20:50 requirements.txt
-rw-r--r--  1 pi pi 4963 Sep 30 20:50 sense_modes.py
-rw-r--r--  1 pi pi  631 Sep 30 20:50 utils.py
drwxr-xr-x  5 pi pi 4096 Sep 30 21:09 .venv
pi@pi:~/pi_productivity $ rm env.example
rm: cannot remove 'env.example': No such file or directory
pi@pi:~/pi_productivity $ rm .env.example
pi@pi:~/pi_productivity $ ls -la
total 64
drwxr-xr-x  4 pi pi 4096 Sep 30 21:12 .
drwx------ 17 pi pi 4096 Sep 30 20:50 ..
-rw-r--r--  1 pi pi 2134 Sep 30 20:50 camera_posture.py
-rw-r--r--  1 pi pi  184 Sep 30 21:06 .env
-rw-r--r--  1 pi pi 2366 Sep 30 20:50 epaper_display.py
-rw-r--r--  1 pi pi 5745 Sep 30 20:50 main.py
-rw-r--r--  1 pi pi 3866 Sep 30 20:50 motion_client.py
-rw-r--r--  1 pi pi 1299 Sep 30 20:50 ocr_notes.py
drwxr-xr-x  2 pi pi 4096 Sep 30 21:10 __pycache__
-rw-r--r--  1 pi pi  816 Sep 30 20:50 README.md
-rw-r--r--  1 pi pi  144 Sep 30 20:50 requirements.txt
-rw-r--r--  1 pi pi 4963 Sep 30 20:50 sense_modes.py
-rw-r--r--  1 pi pi  631 Sep 30 20:50 utils.py
drwxr-xr-x  5 pi pi 4096 Sep 30 21:09 .venv
pi@pi:~/pi_productivity $ sudo apt update
sudo apt install -y python3-sense-hat python3-rtimulib
Hit:1 http://deb.debian.org/debian bookworm InRelease
Hit:2 http://deb.debian.org/debian-security bookworm-security InRelease
Hit:3 http://deb.debian.org/debian bookworm-updates InRelease
Hit:4 http://archive.raspberrypi.com/debian bookworm InRelease
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
5 packages can be upgraded. Run 'apt list --upgradable' to see them.
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
python3-sense-hat is already the newest version (2.6.0-1).
python3-sense-hat set to manually installed.
python3-rtimulib is already the newest version (7.2.1-6+bookworm).
python3-rtimulib set to manually installed.
The following packages were automatically installed and are no longer required:
  libbasicusageenvironment1 libgroupsock8 liblivemedia77 python3-v4l2
Use 'sudo apt autoremove' to remove them.
0 upgraded, 0 newly installed, 0 to remove and 5 not upgraded.
pi@pi:~/pi_productivity $ cd ~/pi_productivity
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
(.venv) pi@pi:~/pi_productivity $ pip uninstall -y sense-hat || true
Found existing installation: sense-hat 2.6.0
Uninstalling sense-hat-2.6.0:
  Successfully uninstalled sense-hat-2.6.0
(.venv) pi@pi:~/pi_productivity $ pip install -r requirements.txt
Looking in indexes: https://pypi.org/simple, https://www.piwheels.org/simple
Requirement already satisfied: python-dotenv==1.0.1 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 2)) (1.0.1)
Requirement already satisfied: requests==2.32.3 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 3)) (2.32.3)
Requirement already satisfied: pillow==10.4.0 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 4)) (10.4.0)
Requirement already satisfied: sense-hat==2.6.0 in /usr/lib/python3/dist-packages (from -r requirements.txt (line 5)) (2.6.0)
Requirement already satisfied: tzdata==2024.1 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 6)) (2024.1)
Requirement already satisfied: pytz==2024.1 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 7)) (2024.1)
Requirement already satisfied: opencv-python==4.10.0.84 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 8)) (4.10.0.84)
Requirement already satisfied: pytesseract==0.3.13 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 9)) (0.3.13)
Requirement already satisfied: charset-normalizer<4,>=2 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (3.4.3)
Requirement already satisfied: idna<4,>=2.5 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (2.5.0)
Requirement already satisfied: certifi>=2017.4.17 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (2025.8.3)
Requirement already satisfied: numpy>=1.21.2 in ./.venv/lib/python3.11/site-packages (from opencv-python==4.10.0.84->-r requirements.txt (line 8)) (2.3.3)
Requirement already satisfied: packaging>=21.3 in ./.venv/lib/python3.11/site-packages (from pytesseract==0.3.13->-r requirements.txt (line 9)) (25.0)
(.venv) pi@pi:~/pi_productivity $ python - <<'PY'
from sense_hat import SenseHat
s=SenseHat(); s.low_light=True
s.clear(0,255,0)
import time; time.sleep(1)
s.clear()
print("Sense HAT OK")
PY
Sense HAT OK
(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 9, in <module>
    from picamera2 import Picamera2
  File "/usr/lib/python3/dist-packages/picamera2/__init__.py", line 11, in <module>
    from .picamera2 import Picamera2, Preview
  File "/usr/lib/python3/dist-packages/picamera2/picamera2.py", line 30, in <module>
    from picamera2.encoders import Encoder, H264Encoder, MJPEGEncoder, Quality
  File "/usr/lib/python3/dist-packages/picamera2/encoders/__init__.py", line 7, in <module>
    from .encoder import Encoder, Quality
  File "/usr/lib/python3/dist-packages/picamera2/encoders/encoder.py", line 13, in <module>
    from ..request import _MappedBuffer
  File "/usr/lib/python3/dist-packages/picamera2/request.py", line 13, in <module>
    import simplejpeg
  File "/usr/lib/python3/dist-packages/simplejpeg/__init__.py", line 1, in <module>
    from ._jpeg import encode_jpeg, encode_jpeg_yuv_planes
  File "simplejpeg/_jpeg.pyx", line 1, in init simplejpeg._jpeg
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject
(.venv) pi@pi:~/pi_productivity $ pip uninstall -y numpy opencv-python simplejpeg
Found existing installation: numpy 2.3.3
Uninstalling numpy-2.3.3:
  Successfully uninstalled numpy-2.3.3
Found existing installation: opencv-python 4.10.0.84
Uninstalling opencv-python-4.10.0.84:
  Successfully uninstalled opencv-python-4.10.0.84
Found existing installation: simplejpeg 1.8.1
Not uninstalling simplejpeg at /usr/lib/python3/dist-packages, outside environment /home/pi/pi_productivity/.venv
Can't uninstall 'simplejpeg'. No files were found to uninstall.
(.venv) pi@pi:~/pi_productivity $ sudo apt update
sudo apt install -y python3-numpy python3-opencv python3-simplejpeg
Hit:1 http://deb.debian.org/debian bookworm InRelease
Hit:2 http://deb.debian.org/debian-security bookworm-security InRelease
Hit:3 http://deb.debian.org/debian bookworm-updates InRelease
Hit:4 http://archive.raspberrypi.com/debian bookworm InRelease
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
5 packages can be upgraded. Run 'apt list --upgradable' to see them.
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
python3-numpy is already the newest version (1:1.24.2-1+deb12u1).
python3-simplejpeg is already the newest version (1.8.1-1).
python3-simplejpeg set to manually installed.
The following packages were automatically installed and are no longer required:
  libbasicusageenvironment1 libgroupsock8 liblivemedia77 python3-v4l2
Use 'sudo apt autoremove' to remove them.
The following additional packages will be installed:
  gdal-data gdal-plugins libaec0 libarmadillo11 libarpack2 libblosc1
  libcfitsio10 libcharls2 libfabric1 libfreexl1 libfyba0 libgdal32 libgdcm3.0
  libgeos-c1v5 libgeos3.11.1 libgeotiff5 libgl2ps1.4 libglew2.2 libhdf4-0-alt
  libhdf5-103-1 libhdf5-hl-100 libjsoncpp25 libkmlbase1 libkmldom1
  libkmlengine1 libmariadb3 libmunge2 libnetcdf19 libodbc2 libodbcinst2
  libogdi4.1 libopencv-contrib406 libopencv-highgui406 libopencv-imgcodecs406
  libopencv-ml406 libopencv-photo406 libopencv-shape406 libopencv-stitching406
  libopencv-video406 libopencv-videoio406 libopencv-viz406 libopenmpi3
  libpmix2 libpq5 libproj25 libqhull-r8.0 libqt5opengl5 librttopo1
  libsocket++1 libspatialite7 libsuperlu5 libsz2 libucx0 liburiparser1
  libvtk9.1 libxerces-c3.2 mariadb-common mysql-common proj-bin proj-data
  unixodbc-common
Suggested packages:
  geotiff-bin gdal-bin libgeotiff-epsg glew-utils libhdf4-doc libhdf4-alt-dev
  hdf4-tools odbc-postgresql tdsodbc ogdi-bin mpi-default-bin vtk9-doc
  vtk9-examples
The following NEW packages will be installed:
  gdal-data gdal-plugins libaec0 libarmadillo11 libarpack2 libblosc1
  libcfitsio10 libcharls2 libfabric1 libfreexl1 libfyba0 libgdal32 libgdcm3.0
  libgeos-c1v5 libgeos3.11.1 libgeotiff5 libgl2ps1.4 libglew2.2 libhdf4-0-alt
  libhdf5-103-1 libhdf5-hl-100 libjsoncpp25 libkmlbase1 libkmldom1
  libkmlengine1 libmariadb3 libmunge2 libnetcdf19 libodbc2 libodbcinst2
  libogdi4.1 libopencv-contrib406 libopencv-highgui406 libopencv-imgcodecs406
  libopencv-ml406 libopencv-photo406 libopencv-shape406 libopencv-stitching406
  libopencv-video406 libopencv-videoio406 libopencv-viz406 libopenmpi3
  libpmix2 libpq5 libproj25 libqhull-r8.0 libqt5opengl5 librttopo1
  libsocket++1 libspatialite7 libsuperlu5 libsz2 libucx0 liburiparser1
  libvtk9.1 libxerces-c3.2 mariadb-common mysql-common proj-bin proj-data
  python3-opencv unixodbc-common
0 upgraded, 62 newly installed, 0 to remove and 5 not upgraded.
Need to get 51.2 MB of archives.
After this operation, 253 MB of additional disk space will be used.
Get:1 http://deb.debian.org/debian bookworm/main arm64 gdal-data all 3.6.2+dfsg-1 [518 kB]
Get:2 http://deb.debian.org/debian bookworm/main arm64 gdal-plugins arm64 3.6.2+dfsg-1+b2 [312 kB]
Get:3 http://deb.debian.org/debian bookworm/main arm64 libaec0 arm64 1.0.6-1+b1 [19.9 kB]
Get:4 http://deb.debian.org/debian bookworm/main arm64 libarpack2 arm64 3.8.0-3 [79.5 kB]
Get:5 http://deb.debian.org/debian bookworm/main arm64 libsuperlu5 arm64 5.3.0+dfsg1-2+b1 [141 kB]
Get:6 http://deb.debian.org/debian bookworm/main arm64 libarmadillo11 arm64 1:11.4.2+dfsg-1 [98.7 kB]
Get:7 http://deb.debian.org/debian bookworm/main arm64 libblosc1 arm64 1.21.3+ds-1 [38.6 kB]
Get:8 http://deb.debian.org/debian bookworm/main arm64 libcfitsio10 arm64 4.2.0-3 [510 kB]
Get:9 http://deb.debian.org/debian bookworm/main arm64 libcharls2 arm64 2.4.1-1 [76.1 kB]
Get:10 http://deb.debian.org/debian bookworm/main arm64 libfabric1 arm64 1.17.0-3 [476 kB]
Get:11 http://deb.debian.org/debian bookworm/main arm64 libfreexl1 arm64 1.0.6-2 [28.4 kB]
Get:12 http://deb.debian.org/debian bookworm/main arm64 libfyba0 arm64 4.1.1-8 [105 kB]
Get:13 http://deb.debian.org/debian bookworm/main arm64 libgeos3.11.1 arm64 3.11.1-1 [683 kB]
Get:14 http://deb.debian.org/debian bookworm/main arm64 libgeos-c1v5 arm64 3.11.1-1 [75.6 kB]
Get:15 http://deb.debian.org/debian bookworm/main arm64 proj-data all 9.1.1-1 [6,212 kB]
Get:16 http://deb.debian.org/debian bookworm/main arm64 libproj25 arm64 9.1.1-1+b1 [1,102 kB]
Get:17 http://deb.debian.org/debian bookworm/main arm64 libgeotiff5 arm64 1.7.1-2+b1 [65.3 kB]
Get:18 http://deb.debian.org/debian bookworm/main arm64 libhdf4-0-alt arm64 4.2.15-5 [238 kB]
Get:19 http://deb.debian.org/debian bookworm/main arm64 libsz2 arm64 1.0.6-1+b1 [7,740 B]
Get:20 http://deb.debian.org/debian bookworm/main arm64 libhdf5-103-1 arm64 1.10.8+repack1-1 [1,037 kB]
Get:21 http://deb.debian.org/debian bookworm/main arm64 liburiparser1 arm64 0.9.7+dfsg-2 [40.4 kB]
Get:22 http://deb.debian.org/debian bookworm/main arm64 libkmlbase1 arm64 1.3.0-10 [43.6 kB]
Get:23 http://deb.debian.org/debian bookworm/main arm64 libkmldom1 arm64 1.3.0-10 [139 kB]
Get:24 http://deb.debian.org/debian bookworm/main arm64 libkmlengine1 arm64 1.3.0-10 [67.8 kB]
Get:25 http://deb.debian.org/debian bookworm/main arm64 mysql-common all 5.8+1.1.0 [6,636 B]
Get:26 http://deb.debian.org/debian bookworm/main arm64 mariadb-common all 1:10.11.14-0+deb12u2 [26.3 kB]
Get:27 http://deb.debian.org/debian bookworm/main arm64 libmariadb3 arm64 1:10.11.14-0+deb12u2 [170 kB]
Get:28 http://deb.debian.org/debian bookworm/main arm64 libhdf5-hl-100 arm64 1.10.8+repack1-1 [64.0 kB]
Get:29 http://deb.debian.org/debian bookworm/main arm64 libnetcdf19 arm64 1:4.9.0-3+b1 [448 kB]
Get:30 http://deb.debian.org/debian bookworm/main arm64 libodbc2 arm64 2.3.11-2+deb12u1 [132 kB]
Get:31 http://deb.debian.org/debian bookworm/main arm64 unixodbc-common all 2.3.11-2+deb12u1 [8,172 B]
Get:32 http://deb.debian.org/debian bookworm/main arm64 libodbcinst2 arm64 2.3.11-2+deb12u1 [35.2 kB]
Get:33 http://deb.debian.org/debian bookworm/main arm64 libogdi4.1 arm64 4.1.0+ds-6 [189 kB]
Get:34 http://deb.debian.org/debian bookworm/main arm64 libpq5 arm64 15.14-0+deb12u1 [185 kB]
Get:35 http://deb.debian.org/debian bookworm/main arm64 libqhull-r8.0 arm64 2020.2-5 [230 kB]
Get:36 http://deb.debian.org/debian bookworm/main arm64 librttopo1 arm64 1.1.0-3 [161 kB]
Get:37 http://deb.debian.org/debian bookworm/main arm64 libspatialite7 arm64 5.0.1-3 [1,542 kB]
Get:38 http://deb.debian.org/debian bookworm/main arm64 libxerces-c3.2 arm64 3.2.4+debian-1 [766 kB]
Get:39 http://deb.debian.org/debian bookworm/main arm64 libgdal32 arm64 3.6.2+dfsg-1+b2 [6,676 kB]
Get:40 http://deb.debian.org/debian bookworm/main arm64 libsocket++1 arm64 1.12.13+git20131030.5d039ba-1+b1 [72.6 kB]
Get:41 http://deb.debian.org/debian bookworm/main arm64 libgdcm3.0 arm64 3.0.21-1 [1,998 kB]
Get:42 http://deb.debian.org/debian bookworm/main arm64 libgl2ps1.4 arm64 1.4.2+dfsg1-2 [38.0 kB]
Get:43 http://deb.debian.org/debian bookworm/main arm64 libglew2.2 arm64 2.2.0-4+b1 [167 kB]
Get:44 http://deb.debian.org/debian bookworm/main arm64 libjsoncpp25 arm64 1.9.5-4 [72.3 kB]
Get:45 http://deb.debian.org/debian bookworm/main arm64 libmunge2 arm64 0.5.15-2 [18.8 kB]
Get:46 http://deb.debian.org/debian bookworm/main arm64 libqt5opengl5 arm64 5.15.8+dfsg-11+deb12u3 [140 kB]
Get:47 http://deb.debian.org/debian bookworm/main arm64 libopencv-highgui406 arm64 4.6.0+dfsg-12 [108 kB]
Get:48 http://deb.debian.org/debian bookworm/main arm64 libopencv-imgcodecs406 arm64 4.6.0+dfsg-12 [110 kB]
Get:49 http://deb.debian.org/debian bookworm/main arm64 libopencv-ml406 arm64 4.6.0+dfsg-12 [172 kB]
Get:50 http://deb.debian.org/debian bookworm/main arm64 libopencv-video406 arm64 4.6.0+dfsg-12 [151 kB]
Get:51 http://deb.debian.org/debian bookworm/main arm64 libopencv-contrib406 arm64 4.6.0+dfsg-12 [3,393 kB]
Get:52 http://deb.debian.org/debian bookworm/main arm64 libopencv-photo406 arm64 4.6.0+dfsg-12 [149 kB]
Get:53 http://deb.debian.org/debian bookworm/main arm64 libopencv-shape406 arm64 4.6.0+dfsg-12 [48.7 kB]
Get:54 http://deb.debian.org/debian bookworm/main arm64 libopencv-stitching406 arm64 4.6.0+dfsg-12 [170 kB]
Get:55 http://deb.debian.org/debian bookworm/main arm64 libopencv-videoio406 arm64 4.6.0+dfsg-12 [189 kB]
Get:56 http://deb.debian.org/debian bookworm/main arm64 libpmix2 arm64 4.2.2-1+deb12u1 [554 kB]
Get:57 http://deb.debian.org/debian bookworm/main arm64 libucx0 arm64 1.13.1-1 [734 kB]
Get:58 http://deb.debian.org/debian bookworm/main arm64 libopenmpi3 arm64 4.1.4-3+b1 [2,161 kB]
Get:59 http://deb.debian.org/debian bookworm/main arm64 libvtk9.1 arm64 9.1.0+really9.1.0+dfsg2-5 [16.3 MB]
Get:60 http://deb.debian.org/debian bookworm/main arm64 libopencv-viz406 arm64 4.6.0+dfsg-12 [108 kB]
Get:61 http://deb.debian.org/debian bookworm/main arm64 proj-bin arm64 9.1.1-1+b1 [193 kB]
Get:62 http://deb.debian.org/debian bookworm/main arm64 python3-opencv arm64 4.6.0+dfsg-12 [1,404 kB]
Fetched 51.2 MB in 20s (2,521 kB/s)                                            
Extracting templates from packages: 100%
Selecting previously unselected package gdal-data.
(Reading database ... 150778 files and directories currently installed.)
Preparing to unpack .../00-gdal-data_3.6.2+dfsg-1_all.deb ...
Unpacking gdal-data (3.6.2+dfsg-1) ...
Selecting previously unselected package gdal-plugins.
Preparing to unpack .../01-gdal-plugins_3.6.2+dfsg-1+b2_arm64.deb ...
Unpacking gdal-plugins (3.6.2+dfsg-1+b2) ...
Selecting previously unselected package libaec0:arm64.
Preparing to unpack .../02-libaec0_1.0.6-1+b1_arm64.deb ...
Unpacking libaec0:arm64 (1.0.6-1+b1) ...
Selecting previously unselected package libarpack2:arm64.
Preparing to unpack .../03-libarpack2_3.8.0-3_arm64.deb ...
Unpacking libarpack2:arm64 (3.8.0-3) ...
Selecting previously unselected package libsuperlu5:arm64.
Preparing to unpack .../04-libsuperlu5_5.3.0+dfsg1-2+b1_arm64.deb ...
Unpacking libsuperlu5:arm64 (5.3.0+dfsg1-2+b1) ...
Selecting previously unselected package libarmadillo11.
Preparing to unpack .../05-libarmadillo11_1%3a11.4.2+dfsg-1_arm64.deb ...
Unpacking libarmadillo11 (1:11.4.2+dfsg-1) ...
Selecting previously unselected package libblosc1:arm64.
Preparing to unpack .../06-libblosc1_1.21.3+ds-1_arm64.deb ...
Unpacking libblosc1:arm64 (1.21.3+ds-1) ...
Selecting previously unselected package libcfitsio10:arm64.
Preparing to unpack .../07-libcfitsio10_4.2.0-3_arm64.deb ...
Unpacking libcfitsio10:arm64 (4.2.0-3) ...
Selecting previously unselected package libcharls2:arm64.
Preparing to unpack .../08-libcharls2_2.4.1-1_arm64.deb ...
Unpacking libcharls2:arm64 (2.4.1-1) ...
Selecting previously unselected package libfabric1:arm64.
Preparing to unpack .../09-libfabric1_1.17.0-3_arm64.deb ...
Unpacking libfabric1:arm64 (1.17.0-3) ...
Selecting previously unselected package libfreexl1:arm64.
Preparing to unpack .../10-libfreexl1_1.0.6-2_arm64.deb ...
Unpacking libfreexl1:arm64 (1.0.6-2) ...
Selecting previously unselected package libfyba0:arm64.
Preparing to unpack .../11-libfyba0_4.1.1-8_arm64.deb ...
Unpacking libfyba0:arm64 (4.1.1-8) ...
Selecting previously unselected package libgeos3.11.1:arm64.
Preparing to unpack .../12-libgeos3.11.1_3.11.1-1_arm64.deb ...
Unpacking libgeos3.11.1:arm64 (3.11.1-1) ...
Selecting previously unselected package libgeos-c1v5:arm64.
Preparing to unpack .../13-libgeos-c1v5_3.11.1-1_arm64.deb ...
Unpacking libgeos-c1v5:arm64 (3.11.1-1) ...
Selecting previously unselected package proj-data.
Preparing to unpack .../14-proj-data_9.1.1-1_all.deb ...
Unpacking proj-data (9.1.1-1) ...
Selecting previously unselected package libproj25:arm64.
Preparing to unpack .../15-libproj25_9.1.1-1+b1_arm64.deb ...
Unpacking libproj25:arm64 (9.1.1-1+b1) ...
Selecting previously unselected package libgeotiff5:arm64.
Preparing to unpack .../16-libgeotiff5_1.7.1-2+b1_arm64.deb ...
Unpacking libgeotiff5:arm64 (1.7.1-2+b1) ...
Selecting previously unselected package libhdf4-0-alt.
Preparing to unpack .../17-libhdf4-0-alt_4.2.15-5_arm64.deb ...
Unpacking libhdf4-0-alt (4.2.15-5) ...
Selecting previously unselected package libsz2:arm64.
Preparing to unpack .../18-libsz2_1.0.6-1+b1_arm64.deb ...
Unpacking libsz2:arm64 (1.0.6-1+b1) ...
Selecting previously unselected package libhdf5-103-1:arm64.
Preparing to unpack .../19-libhdf5-103-1_1.10.8+repack1-1_arm64.deb ...
Unpacking libhdf5-103-1:arm64 (1.10.8+repack1-1) ...
Selecting previously unselected package liburiparser1:arm64.
Preparing to unpack .../20-liburiparser1_0.9.7+dfsg-2_arm64.deb ...
Unpacking liburiparser1:arm64 (0.9.7+dfsg-2) ...
Selecting previously unselected package libkmlbase1:arm64.
Preparing to unpack .../21-libkmlbase1_1.3.0-10_arm64.deb ...
Unpacking libkmlbase1:arm64 (1.3.0-10) ...
Selecting previously unselected package libkmldom1:arm64.
Preparing to unpack .../22-libkmldom1_1.3.0-10_arm64.deb ...
Unpacking libkmldom1:arm64 (1.3.0-10) ...
Selecting previously unselected package libkmlengine1:arm64.
Preparing to unpack .../23-libkmlengine1_1.3.0-10_arm64.deb ...
Unpacking libkmlengine1:arm64 (1.3.0-10) ...
Selecting previously unselected package mysql-common.
Preparing to unpack .../24-mysql-common_5.8+1.1.0_all.deb ...
Unpacking mysql-common (5.8+1.1.0) ...
Selecting previously unselected package mariadb-common.
Preparing to unpack .../25-mariadb-common_1%3a10.11.14-0+deb12u2_all.deb ...
Unpacking mariadb-common (1:10.11.14-0+deb12u2) ...
Selecting previously unselected package libmariadb3:arm64.
Preparing to unpack .../26-libmariadb3_1%3a10.11.14-0+deb12u2_arm64.deb ...
Unpacking libmariadb3:arm64 (1:10.11.14-0+deb12u2) ...
Selecting previously unselected package libhdf5-hl-100:arm64.
Preparing to unpack .../27-libhdf5-hl-100_1.10.8+repack1-1_arm64.deb ...
Unpacking libhdf5-hl-100:arm64 (1.10.8+repack1-1) ...
Selecting previously unselected package libnetcdf19:arm64.
Preparing to unpack .../28-libnetcdf19_1%3a4.9.0-3+b1_arm64.deb ...
Unpacking libnetcdf19:arm64 (1:4.9.0-3+b1) ...
Selecting previously unselected package libodbc2:arm64.
Preparing to unpack .../29-libodbc2_2.3.11-2+deb12u1_arm64.deb ...
Unpacking libodbc2:arm64 (2.3.11-2+deb12u1) ...
Selecting previously unselected package unixodbc-common.
Preparing to unpack .../30-unixodbc-common_2.3.11-2+deb12u1_all.deb ...
Unpacking unixodbc-common (2.3.11-2+deb12u1) ...
Selecting previously unselected package libodbcinst2:arm64.
Preparing to unpack .../31-libodbcinst2_2.3.11-2+deb12u1_arm64.deb ...
Unpacking libodbcinst2:arm64 (2.3.11-2+deb12u1) ...
Selecting previously unselected package libogdi4.1.
Preparing to unpack .../32-libogdi4.1_4.1.0+ds-6_arm64.deb ...
Unpacking libogdi4.1 (4.1.0+ds-6) ...
Selecting previously unselected package libpq5:arm64.
Preparing to unpack .../33-libpq5_15.14-0+deb12u1_arm64.deb ...
Unpacking libpq5:arm64 (15.14-0+deb12u1) ...
Selecting previously unselected package libqhull-r8.0:arm64.
Preparing to unpack .../34-libqhull-r8.0_2020.2-5_arm64.deb ...
Unpacking libqhull-r8.0:arm64 (2020.2-5) ...
Selecting previously unselected package librttopo1:arm64.
Preparing to unpack .../35-librttopo1_1.1.0-3_arm64.deb ...
Unpacking librttopo1:arm64 (1.1.0-3) ...
Selecting previously unselected package libspatialite7:arm64.
Preparing to unpack .../36-libspatialite7_5.0.1-3_arm64.deb ...
Unpacking libspatialite7:arm64 (5.0.1-3) ...
Selecting previously unselected package libxerces-c3.2:arm64.
Preparing to unpack .../37-libxerces-c3.2_3.2.4+debian-1_arm64.deb ...
Unpacking libxerces-c3.2:arm64 (3.2.4+debian-1) ...
Selecting previously unselected package libgdal32.
Preparing to unpack .../38-libgdal32_3.6.2+dfsg-1+b2_arm64.deb ...
Unpacking libgdal32 (3.6.2+dfsg-1+b2) ...
Selecting previously unselected package libsocket++1:arm64.
Preparing to unpack .../39-libsocket++1_1.12.13+git20131030.5d039ba-1+b1_arm64.deb ...
Unpacking libsocket++1:arm64 (1.12.13+git20131030.5d039ba-1+b1) ...
Selecting previously unselected package libgdcm3.0:arm64.
Preparing to unpack .../40-libgdcm3.0_3.0.21-1_arm64.deb ...
Unpacking libgdcm3.0:arm64 (3.0.21-1) ...
Selecting previously unselected package libgl2ps1.4.
Preparing to unpack .../41-libgl2ps1.4_1.4.2+dfsg1-2_arm64.deb ...
Unpacking libgl2ps1.4 (1.4.2+dfsg1-2) ...
Selecting previously unselected package libglew2.2:arm64.
Preparing to unpack .../42-libglew2.2_2.2.0-4+b1_arm64.deb ...
Unpacking libglew2.2:arm64 (2.2.0-4+b1) ...
Selecting previously unselected package libjsoncpp25:arm64.
Preparing to unpack .../43-libjsoncpp25_1.9.5-4_arm64.deb ...
Unpacking libjsoncpp25:arm64 (1.9.5-4) ...
Selecting previously unselected package libmunge2.
Preparing to unpack .../44-libmunge2_0.5.15-2_arm64.deb ...
Unpacking libmunge2 (0.5.15-2) ...
Selecting previously unselected package libqt5opengl5:arm64.
Preparing to unpack .../45-libqt5opengl5_5.15.8+dfsg-11+deb12u3_arm64.deb ...
Unpacking libqt5opengl5:arm64 (5.15.8+dfsg-11+deb12u3) ...
Selecting previously unselected package libopencv-highgui406:arm64.
Preparing to unpack .../46-libopencv-highgui406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-highgui406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-imgcodecs406:arm64.
Preparing to unpack .../47-libopencv-imgcodecs406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-imgcodecs406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-ml406:arm64.
Preparing to unpack .../48-libopencv-ml406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-ml406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-video406:arm64.
Preparing to unpack .../49-libopencv-video406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-video406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-contrib406:arm64.
Preparing to unpack .../50-libopencv-contrib406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-contrib406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-photo406:arm64.
Preparing to unpack .../51-libopencv-photo406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-photo406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-shape406:arm64.
Preparing to unpack .../52-libopencv-shape406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-shape406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-stitching406:arm64.
Preparing to unpack .../53-libopencv-stitching406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-stitching406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libopencv-videoio406:arm64.
Preparing to unpack .../54-libopencv-videoio406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-videoio406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package libpmix2:arm64.
Preparing to unpack .../55-libpmix2_4.2.2-1+deb12u1_arm64.deb ...
Unpacking libpmix2:arm64 (4.2.2-1+deb12u1) ...
Selecting previously unselected package libucx0:arm64.
Preparing to unpack .../56-libucx0_1.13.1-1_arm64.deb ...
Unpacking libucx0:arm64 (1.13.1-1) ...
Selecting previously unselected package libopenmpi3:arm64.
Preparing to unpack .../57-libopenmpi3_4.1.4-3+b1_arm64.deb ...
Unpacking libopenmpi3:arm64 (4.1.4-3+b1) ...
Selecting previously unselected package libvtk9.1:arm64.
Preparing to unpack .../58-libvtk9.1_9.1.0+really9.1.0+dfsg2-5_arm64.deb ...
Unpacking libvtk9.1:arm64 (9.1.0+really9.1.0+dfsg2-5) ...
Selecting previously unselected package libopencv-viz406:arm64.
Preparing to unpack .../59-libopencv-viz406_4.6.0+dfsg-12_arm64.deb ...
Unpacking libopencv-viz406:arm64 (4.6.0+dfsg-12) ...
Selecting previously unselected package proj-bin.
Preparing to unpack .../60-proj-bin_9.1.1-1+b1_arm64.deb ...
Unpacking proj-bin (9.1.1-1+b1) ...
Selecting previously unselected package python3-opencv:arm64.
Preparing to unpack .../61-python3-opencv_4.6.0+dfsg-12_arm64.deb ...
Unpacking python3-opencv:arm64 (4.6.0+dfsg-12) ...
Setting up libfabric1:arm64 (1.17.0-3) ...
Setting up mysql-common (5.8+1.1.0) ...
update-alternatives: using /etc/mysql/my.cnf.fallback to provide /etc/mysql/my.cnf (my.cnf) in auto mode
Setting up libopencv-ml406:arm64 (4.6.0+dfsg-12) ...
Setting up libucx0:arm64 (1.13.1-1) ...
Setting up libxerces-c3.2:arm64 (3.2.4+debian-1) ...
Setting up proj-data (9.1.1-1) ...
Setting up libgeos3.11.1:arm64 (3.11.1-1) ...
Setting up libproj25:arm64 (9.1.1-1+b1) ...
Setting up libogdi4.1 (4.1.0+ds-6) ...
Setting up libcharls2:arm64 (2.4.1-1) ...
Setting up libopencv-photo406:arm64 (4.6.0+dfsg-12) ...
Setting up libarpack2:arm64 (3.8.0-3) ...
Setting up libpq5:arm64 (15.14-0+deb12u1) ...
Setting up libsuperlu5:arm64 (5.3.0+dfsg1-2+b1) ...
Setting up proj-bin (9.1.1-1+b1) ...
Setting up libqhull-r8.0:arm64 (2020.2-5) ...
Setting up libcfitsio10:arm64 (4.2.0-3) ...
Setting up libaec0:arm64 (1.0.6-1+b1) ...
Setting up gdal-data (3.6.2+dfsg-1) ...
Setting up libopencv-video406:arm64 (4.6.0+dfsg-12) ...
Setting up libgl2ps1.4 (1.4.2+dfsg1-2) ...
Setting up libgeotiff5:arm64 (1.7.1-2+b1) ...
Setting up mariadb-common (1:10.11.14-0+deb12u2) ...
update-alternatives: using /etc/mysql/mariadb.cnf to provide /etc/mysql/my.cnf (my.cnf) in auto mode
Setting up libopencv-stitching406:arm64 (4.6.0+dfsg-12) ...
Setting up libmunge2 (0.5.15-2) ...
Setting up libjsoncpp25:arm64 (1.9.5-4) ...
Setting up libgeos-c1v5:arm64 (3.11.1-1) ...
Setting up libmariadb3:arm64 (1:10.11.14-0+deb12u2) ...
Setting up unixodbc-common (2.3.11-2+deb12u1) ...
Setting up libsocket++1:arm64 (1.12.13+git20131030.5d039ba-1+b1) ...
Setting up libglew2.2:arm64 (2.2.0-4+b1) ...
Setting up libopencv-shape406:arm64 (4.6.0+dfsg-12) ...
Setting up libhdf4-0-alt (4.2.15-5) ...
Setting up libodbc2:arm64 (2.3.11-2+deb12u1) ...
Setting up liburiparser1:arm64 (0.9.7+dfsg-2) ...
Setting up librttopo1:arm64 (1.1.0-3) ...
Setting up libfreexl1:arm64 (1.0.6-2) ...
Setting up libqt5opengl5:arm64 (5.15.8+dfsg-11+deb12u3) ...
Setting up libfyba0:arm64 (4.1.1-8) ...
Setting up libkmlbase1:arm64 (1.3.0-10) ...
Setting up libblosc1:arm64 (1.21.3+ds-1) ...
Setting up libsz2:arm64 (1.0.6-1+b1) ...
Setting up gdal-plugins (3.6.2+dfsg-1+b2) ...
Setting up libkmldom1:arm64 (1.3.0-10) ...
Setting up libopencv-highgui406:arm64 (4.6.0+dfsg-12) ...
Setting up libspatialite7:arm64 (5.0.1-3) ...
Setting up libodbcinst2:arm64 (2.3.11-2+deb12u1) ...
Setting up libkmlengine1:arm64 (1.3.0-10) ...
Setting up libarmadillo11 (1:11.4.2+dfsg-1) ...
Setting up libpmix2:arm64 (4.2.2-1+deb12u1) ...
Setting up libopenmpi3:arm64 (4.1.4-3+b1) ...
Setting up libgdcm3.0:arm64 (3.0.21-1) ...
Setting up libhdf5-103-1:arm64 (1.10.8+repack1-1) ...
Setting up libhdf5-hl-100:arm64 (1.10.8+repack1-1) ...
Setting up libnetcdf19:arm64 (1:4.9.0-3+b1) ...
Setting up libgdal32 (3.6.2+dfsg-1+b2) ...
Setting up libvtk9.1:arm64 (9.1.0+really9.1.0+dfsg2-5) ...
Setting up libopencv-viz406:arm64 (4.6.0+dfsg-12) ...
Setting up libopencv-imgcodecs406:arm64 (4.6.0+dfsg-12) ...
Setting up libopencv-videoio406:arm64 (4.6.0+dfsg-12) ...
Setting up libopencv-contrib406:arm64 (4.6.0+dfsg-12) ...
Setting up python3-opencv:arm64 (4.6.0+dfsg-12) ...
Processing triggers for man-db (2.11.2-2) ...
Processing triggers for libc-bin (2.36-9+rpt2+deb12u12) ...
(.venv) pi@pi:~/pi_productivity $ sed -i 's/^opencv-python/#opencv-python (usando python3-opencv do sistema)/' requirements.txt
(.venv) pi@pi:~/pi_productivity $ pip install -r requirements.txt
Looking in indexes: https://pypi.org/simple, https://www.piwheels.org/simple
Requirement already satisfied: python-dotenv==1.0.1 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 2)) (1.0.1)
Requirement already satisfied: requests==2.32.3 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 3)) (2.32.3)
Requirement already satisfied: pillow==10.4.0 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 4)) (10.4.0)
Requirement already satisfied: sense-hat==2.6.0 in /usr/lib/python3/dist-packages (from -r requirements.txt (line 5)) (2.6.0)
Requirement already satisfied: tzdata==2024.1 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 6)) (2024.1)
Requirement already satisfied: pytz==2024.1 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 7)) (2024.1)
Requirement already satisfied: pytesseract==0.3.13 in ./.venv/lib/python3.11/site-packages (from -r requirements.txt (line 9)) (0.3.13)
Requirement already satisfied: charset-normalizer<4,>=2 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (3.4.3)
Requirement already satisfied: idna<4,>=2.5 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (2.5.0)
Requirement already satisfied: certifi>=2017.4.17 in ./.venv/lib/python3.11/site-packages (from requests==2.32.3->-r requirements.txt (line 3)) (2025.8.3)
Requirement already satisfied: packaging>=21.3 in ./.venv/lib/python3.11/site-packages (from pytesseract==0.3.13->-r requirements.txt (line 9)) (25.0)
(.venv) pi@pi:~/pi_productivity $ python - <<'PY'
import numpy, simplejpeg
from picamera2 import Picamera2
print("OK:", "numpy", numpy.__version__)
PY
OK: numpy 1.24.2
(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 165, in <module>
    App().run()
    ^^^^^
  File "/home/pi/pi_productivity/main.py", line 32, in __init__
    self.posture = PostureMonitor(PostureConfig())
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/pi/pi_productivity/camera_posture.py", line 18, in __init__
    self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                                              ^^^^^^^^
AttributeError: module 'cv2' has no attribute 'data'
(.venv) pi@pi:~/pi_productivity $ sudo apt update
sudo apt install -y libopencv-data
Hit:1 http://deb.debian.org/debian bookworm InRelease
Hit:2 http://deb.debian.org/debian-security bookworm-security InRelease
Hit:3 http://deb.debian.org/debian bookworm-updates InRelease
Hit:4 http://archive.raspberrypi.com/debian bookworm InRelease   
Reading package lists... Done                                    
Building dependency tree... Done
Reading state information... Done
5 packages can be upgraded. Run 'apt list --upgradable' to see them.
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
E: Unable to locate package libopencv-data
(.venv) pi@pi:~/pi_productivity $ sudo apt install -y libopencv- data
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
E: Unable to locate package libopencv
E: Unable to locate package data
(.venv) pi@pi:~/pi_productivity $ sudo apt install -y libopencv -data
E: Command line option 'a' [from -data] is not understood in combination with the other options.
(.venv) pi@pi:~/pi_productivity $ sudo apt install -y libopencv-data
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
E: Unable to locate package libopencv-data
(.venv) pi@pi:~/pi_productivity $ python - <<'PY'
import camera_posture
print("camera_posture OK")
PY
camera_posture OK
(.venv) pi@pi:~/pi_productivity $ python main.py

Traceback (most recent call last):
  File "/usr/lib/python3.11/pathlib.py", line 1117, in mkdir
    os.mkdir(self, mode)
FileNotFoundError: [Errno 2] No such file or directory: '/mnt/data/pi_productivity/notes'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.11/pathlib.py", line 1117, in mkdir
    os.mkdir(self, mode)
FileNotFoundError: [Errno 2] No such file or directory: '/mnt/data/pi_productivity'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 165, in <module>
    App().run()
    ^^^^^
  File "/home/pi/pi_productivity/main.py", line 33, in __init__
    self.ocr = OCRNotes(OCRConfig())
               ^^^^^^^^^^^^^^^^^^^^^
  File "/home/pi/pi_productivity/ocr_notes.py", line 17, in __init__
    Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)
  File "/usr/lib/python3.11/pathlib.py", line 1121, in mkdir
    self.parent.mkdir(parents=True, exist_ok=True)
  File "/usr/lib/python3.11/pathlib.py", line 1121, in mkdir
    self.parent.mkdir(parents=True, exist_ok=True)
  File "/usr/lib/python3.11/pathlib.py", line 1117, in mkdir
    os.mkdir(self, mode)
PermissionError: [Errno 13] Permission denied: '/mnt/data'
(.venv) pi@pi:~/pi_productivity $ 
(.venv) pi@pi:~/pi_productivity $ source .venv/bin/activate
python main.py
Erro ao atualizar tarefas: 401 Client Error: Unauthorized for url: https://api.usemotion.com/v1/tasks?limit=200
Erro ao atualizar tarefas: 401 Client Error: Unauthorized for url: https://api.usemotion.com/v1/tasks?limit=200
^[[A^[[A`^[^[^[^CTraceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 165, in <module>
    App().run()
  File "/home/pi/pi_productivity/main.py", line 162, in run
    time.sleep(1)
KeyboardInterrupt

(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 4, in <module>
    from motion_client import MotionClient
  File "/home/pi/pi_productivity/motion_client.py", line 14
    self.sess.headers.update({"X-API-Key": API_KEY})
TabError: inconsistent use of tabs and spaces in indentation
(.venv) pi@pi:~/pi_productivity $ python main.py
Erro ao atualizar tarefas: 400 Client Error: Bad Request for url: https://api.usemotion.com/v1/tasks?limit=200
Erro ao atualizar tarefas: 400 Client Error: Bad Request for url: https://api.usemotion.com/v1/tasks?limit=200
^CTraceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 165, in <module>
    App().run()
  File "/home/pi/pi_productivity/main.py", line 162, in run
    time.sleep(1)
KeyboardInterrupt

(.venv) pi@pi:~/pi_productivity $ nano motion_client.py
(.venv) pi@pi:~/pi_productivity $ python main.py
Erro ao atualizar tarefas: 'dict' object has no attribute 'lower'
Erro ao atualizar tarefas: 'dict' object has no attribute 'lower'
^CTraceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 165, in <module>
    App().run()
  File "/home/pi/pi_productivity/main.py", line 162, in run
    time.sleep(1)
KeyboardInterrupt

(.venv) pi@pi:~/pi_productivity $ nano motion_client.py
(.venv) pi@pi:~/pi_productivity $ nano motion_client.py
(.venv) pi@pi:~/pi_productivity $ nano motion_client.py
(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 4, in <module>
    from motion_client import MotionClient
  File "/home/pi/pi_productivity/motion_client.py", line 67
    d = parse_iso_date(t.get("startDate") or 
IndentationError: unexpected indent
(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 4, in <module>
    from motion_client import MotionClient
  File "/home/pi/pi_productivity/motion_client.py", line 67
    d = parse_iso_date(t.get("startDate") or 
IndentationError: unexpected indent
(.venv) pi@pi:~/pi_productivity $ python main.py
Traceback (most recent call last):
  File "/home/pi/pi_productivity/main.py", line 165, in <module>
    App().run()
    ^^^^^
  File "/home/pi/pi_productivity/main.py", line 21, in __init__
    self.motion = MotionClient()
                  ^^^^^^^^^^^^^^
  File "/home/pi/pi_productivity/motion_client.py", line 11, in __init__
    raise RuntimeError("Defina MOTION_API_KEY no arquivo .env")
RuntimeError: Defina MOTION_API_KEY no arquivo .env
(.venv) pi@pi:~/pi_productivity $ dismount
-bash: dismount: command not found
(.venv) pi@pi:~/pi_productivity $ cd
(.venv) pi@pi:~ $ disclose
-bash: disclose: command not found
(.venv) pi@pi:~ $ deactivate
pi@pi:~ $ ls -la ~/pi_productivity/.env
-rw-r--r-- 1 pi pi 184 Sep 30 21:06 /home/pi/pi_productivity/.env
pi@pi:~ $ source .venv/bin/activate
(.venv) pi@pi:~ $ dactivate
-bash: dactivate: command not found
(.venv) pi@pi:~ $ deactivate
pi@pi:~ $ xdg-open /home/pi/pi_productivity/last_epaper.png
Error: no "view" rule for type "image/png" passed its test case
       (for more information, add "--debug=1" on the command line)
pi@pi:~ $ xdg-open /home/pi/pi_productivity/last_epaper.png
Error: no "view" rule for type "image/png" passed its test case
       (for more information, add "--debug=1" on the command line)
pi@pi:~ $ xdg-open /home/pi/pi_productivity/last_epaper.png
Error: no "view" rule for type "image/png" passed its test case
       (for more information, add "--debug=1" on the command line)
pi@pi:~ $ xdg-open /home/pi/pi_productivity/last_epaper.png
Error: no "view" rule for type "image/png" passed its test case
       (for more information, add "--debug=1" on the command line)
pi@pi:~ $ xdg-open /home/pi/pi_productivity/last_epaper.png
Error: no "view" rule for type "image/png" passed its test case
       (for more information, add "--debug=1" on the command line)
               Download Options (Lynx Version 2.9.0dev.12), help

Downloaded link: file://localhost/home/pi/pi_productivity/last_epaper.png
Suggested file name: last_epaper.png

Standard download options:
   Save to disk

Local additions:


Press <return> to finish: 
               Download Options (Lynx Version 2.9.0dev.12), help

Downloaded link: file://localhost/home/pi/pi_productivity/last_epaper.png
Suggested file name: last_epaper.png

Standard download options:
   Save to disk

Local additions:


Press <return> to finish: ^[OA^[OA^[OB^[OB
               Download Options (Lynx Version 2.9.0dev.12), help

Downloaded link: file://localhost/home/pi/pi_productivity/last_epaper.png
Suggested file name: last_epaper.png

Standard download options:
   Save to disk

Local additions:


Press <return> to finish: 
               Download Options (Lynx Version 2.9.0dev.12), help

Downloaded link: file://localhost/home/pi/pi_productivity/last_epaper.png
Suggested file name: last_epaper.png

Standard download options:
   Save to disk

Local additions:


Press <return> to finish: ^[OB^[OA^[OD
pi@pi:~ $ file://localhost/home/pi/pi_productivity/last_epaper.png
-bash: file://localhost/home/pi/pi_productivity/last_epaper.png: No such file or directory
pi@pi:~ $ scp pi@192.168.0.9:/home/pi/pi_productivity/last_epaper.png  
usage: scp [-346ABCOpqRrsTv] [-c cipher] [-D sftp_server_path] [-F ssh_config]
           [-i identity_file] [-J destination] [-l limit] [-o ssh_option]
           [-P port] [-S program] [-X sftp_option] source ... target
pi@pi:~ $ scp pi@192.168.0.9:/home/pi/pi_productivity/last_epaper.png
usage: scp [-346ABCOpqRrsTv] [-c cipher] [-D sftp_server_path] [-F ssh_config]
           [-i identity_file] [-J destination] [-l limit] [-o ssh_option]
           [-P port] [-S program] [-X sftp_option] source ... target
pi@pi:~ $ xdg-open /home/pi/pi_productivity/last_epaper.png
Error: no "view" rule for type "image/png" passed its test case
       (for more information, add "--debug=1" on the command line)
pi@pi:~ $ scp pi@192.168.0.9:/home/pi/pi_productivity/last_epaper.png
usage: scp [-346ABCOpqRrsTv] [-c cipher] [-D sftp_server_path] [-F ssh_config]
           [-i identity_file] [-J destination] [-l limit] [-o ssh_option]
           [-P port] [-S program] [-X sftp_option] source ... target
pi@pi:~ $ nano ~/pi_productivity/.env
pi@pi:~ $ nano ~/pi_productivity/main.py
pi@pi:~ $ nano ~/pi_productivity/main.py

  GNU nano 7.2                                                                               /home/pi/pi_productivity/main.py                                                                                        
                row = []
                for x in range(8):
                    row.append(R if (x==3 or y==3) else BLACK)
                rows.append(row)
        elif name == "OCR NOTAS":
            rows = [[BLACK]*8 for _ in range(8)]
            for y in range(2,6):
                rows[y][2] = C; rows[y][5] = C
            for x in range(2,6):
                rows[2][x] = C; rows[5][x] = C
            rows[3][3] = C; rows[4][4] = C
        else:
            rows = [[W]*8 for _ in range(8)]
        set_pixels(rows)

    # ——— Hidratação (gota azul-clara) ———
    def _show_hydration_drop(self):
        from sense_modes import sense
        BLACK = [0,0,0]
        DROP  = [0,180,255]
        rows = [[BLACK]*8 for _ in range(8)]
        coords = [(1,3,4),(2,2,5),(3,2,5),(4,3,4),(5,3,4),(6,3,4)]
        for y,x0,x1 in coords:
            for x in range(x0, x1+1):
                rows[y][x] = DROP
        flat = []
        for row in rows: flat.extend(row)
        sense.set_pixels(flat)

    def _hydrate_blink(self):
        from sense_modes import sense
        import time as _t
        for _ in range(max(1, HYDRATE_FLASHES)):
            self._show_hydration_drop()
            _t.sleep(HYDRATE_ON_SEC)
            sense.clear()
            _t.sleep(HYDRATE_OFF_SEC)
        self._show_mode_pattern(self.MODES[self.mode_index])

    def _hydrate_loop(self):
        import time as _t
        next_ts = _t.time() + HYDRATE_INTERVAL_MIN*60
        while True:
            _t.sleep(1)
            if _t.time() >= next_ts:
                try:
                    print("[Hydrate] lembrete de hidratação")
                    self._hydrate_blink()
                except Exception as e:
                    print("[Hydrate] erro:", e)
                next_ts = _t.time() + HYDRATE_INTERVAL_MIN*60

    def run(self):
        self._render_mode_banner()
        sense.stick.direction_any = self.handle_joystick
        while True:
            self.maybe_poll_motion()
            time.sleep(1)

if __name__ == "__main__":
    App().run()
