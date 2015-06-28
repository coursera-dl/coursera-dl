# HOW TO LAUNCH CONTAINER:

1. [optional] Insert your username and password
   to `.netrc` file if your plan to use `-n` option
   (edit template in this directory).
2. Build Docker image:
   `./build.sh`
3. Run Docker container to download courses A, B and C:
   `./download.sh A B C`
4. All courses will be downloaded in directory `~/courses`
