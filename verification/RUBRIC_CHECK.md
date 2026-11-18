# Resubmission evidence — rubric 2637

Current classroom rubric reviewed November 18, 2026, Server Deployment and Containerization 3.1.0, project lesson e45a4bbc-a12b-4810-b6d1-6fde9589ae34. Prior review: 4875912.

| Criterion | Verified evidence |
|---|---|
| Dockerfile compiles locally | `docker-build.log`: successful linux/amd64 build with Docker Desktop. |
| Correct Docker instructions | Root Dockerfile uses exact `FROM python:stretch` and `ENTRYPOINT ["gunicorn", "-b", ":8080", "main:APP"]`. |
| Docker image runs; all endpoints respond | `docker-http.txt`: GET `/`, POST `/auth`, GET `/contents`, and two invalid-auth checks passed through Gunicorn. `docker-pytest.log`: 5/5 tests passed inside the image. |
| JWT_SECRET set in a file | `.env_file.example` is supplied. Reproducible probe creates a temporary env file, supplies it with `--env-file`, and verifies the JWT signature uses that value. Real secrets are not committed. |
| CodeBuild reads Parameter Store | `buildspec.yml` maps `JWT_SECRET` under `env.parameter-store`; successful build log confirms Parameter Store decryption and secret application. |
| CloudFormation defaults | `ci-cd-codepipeline.cfn.yml`: EKS `simple-jwt-api`, source repo `cd0157-Server-Deployment-and-Containerization`, user `sd3093`, role `UdacityFlaskDeployCBKubectlRole`, branch `master`. |
| External address in reviewer notes | Public ELB hostname is in README; use the same full HTTP URL in Udacity's submission notes. |
| API runs from EKS | `live-endpoints.json`: HTTP 200 for all three required endpoints; `final-deployment.json`: 3 ready/updated replicas of the c6151ec0 image; AWS build screenshot and log show successful rollout. |
| Tests run in CodeBuild | `buildspec.yml` runs `python -m pytest test_main.py` before building/deploying. Actual `codebuild-log.txt` records 5 passed. |

The base image is obsolete but explicitly required by this historical rubric. It is used for this course exercise, not recommended for a new production service. Saved deployment evidence validates implementation commit c6151ec0; subsequent evidence-only updates preserve application behavior.
