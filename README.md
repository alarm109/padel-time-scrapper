Run this command to build and deploy updated python script

```sh
cd terraform
terraform apply -target=null_resource.build_image -target=google_cloud_run_v2_job.padel_checker
```