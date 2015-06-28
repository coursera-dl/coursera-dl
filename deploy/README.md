# How to launch the container

1. [optional] Insert your username and password in the `.netrc` file if you
   plan to use the `-n` optionof `coursera-dl` (edit template in this
   directory).
2. Build Docker image:
   `./build.sh`
3. Run Docker container to download courses A, B and C:
   `./download.sh A B C`
4. All courses will be downloaded in directory `~/courses`
