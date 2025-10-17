docker run -p 8501:8501 ^
  -e DB_USER=c##tester ^
  -e DB_PASSWORD=learner123^
  -e DB_DSN=host.docker.internal:1521/FREE ^
  --name restaurant-container ^
  --security-opt seccomp=unconfined ^
  restaurant-app