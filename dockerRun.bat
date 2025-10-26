docker run -p 8501:8501 ^
  -e DB_USER=c##tester ^
  -e DB_PASSWORD=learner123^
  -e DB_DSN=host.docker.internal:1521/FREE ^
  -e SMTP_HOST=smtp.gmail.com ^
  -e SMTP_PORT=587 ^
  -e EMAIL_USER=unixanand2005@gmail.com ^
  -e EMAIL_PASS=rgdnbermfphvasve ^
  -e ALERT_RECIPIENT=unix_anand@outlook.com ^
  -e SEND_ALERTS=true ^
  --name restaurant-container ^
  --security-opt seccomp=unconfined ^
  restaurant-app