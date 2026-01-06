# syntax=docker/dockerfile:1
FROM node:20 as builder

# Build React app - context is now at alex-django/
WORKDIR /react-build
COPY fitness-frontend/package.json ./
COPY fitness-frontend/.env.production ./
RUN npm install --legacy-peer-deps
COPY fitness-frontend/ .
# Source environment variables and build
RUN set -a && . ./.env.production && set +a && npm run build || echo "Warning: React build failed, will retry at runtime"

# Final stage - Node.js with Python
FROM node:20

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code

COPY docker/requirements.txt /code/
RUN pip3 install --break-system-packages -r /code/requirements.txt

# Copy entire project
COPY . /code/

# Copy entrypoint script
COPY docker/entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# Create static/fitness directory
RUN mkdir -p /code/static/fitness

# Try to copy React build from builder stage if it exists
COPY --from=builder /react-build/dist/ /code/static/fitness/

EXPOSE 80
CMD ["bash", "/code/entrypoint.sh"]
