FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy all static website files, subdirectories, and legal documents
COPY . /usr/share/nginx/html/

# Ensure proper permissions for Nginx worker process
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
