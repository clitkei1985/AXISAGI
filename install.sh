#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    color=$1
    message=$2
    printf "${color}${message}${NC}\n"
}

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    print_color $YELLOW "Please run as root or with sudo"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    if command_exists python3; then
        python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if (( $(echo "$python_version >= 3.8" | bc -l) )); then
            print_color $GREEN "Python $python_version found"
            return 0
        fi
    fi
    print_color $RED "Python 3.8 or higher is required"
    exit 1
}

# Check for CUDA support
check_cuda() {
    if command_exists nvidia-smi; then
        print_color $GREEN "NVIDIA GPU detected"
        cuda_version=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader)
        print_color $GREEN "CUDA Version: $cuda_version"
        # Update requirements.txt to use CUDA versions
        sed -i 's/faiss-cpu/faiss-gpu/g' requirements.txt
        sed -i 's/torch>=/torch+cu11>=/g' requirements.txt
    else
        print_color $YELLOW "No NVIDIA GPU detected, using CPU only"
    fi
}

# Install system dependencies
install_system_deps() {
    print_color $GREEN "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3-pip \
        python3-venv \
        ffmpeg \
        libsndfile1 \
        portaudio19-dev \
        postgresql \
        postgresql-contrib \
        redis-server \
        nginx \
        supervisor
        
    print_color $GREEN "System dependencies installed"
}

# Create Python virtual environment
create_venv() {
    print_color $GREEN "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    print_color $GREEN "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_color $GREEN "Installing Python dependencies..."
    pip install -r requirements.txt
    print_color $GREEN "Python dependencies installed"
}

# Create necessary directories
create_directories() {
    print_color $GREEN "Creating necessary directories..."
    
    # Create directories
    mkdir -p db/backups
    mkdir -p uploads/{audio,images,datasets}
    mkdir -p logs
    mkdir -p plugins
    
    # Set permissions
    chown -R $SUDO_USER:$SUDO_USER .
    chmod -R 755 .
    
    print_color $GREEN "Directories created"
}

# Initialize database
init_database() {
    print_color $GREEN "Initializing database..."
    
    # Create database if using PostgreSQL
    if grep -q "postgresql" config.yaml; then
        su - postgres -c "createdb axis"
        print_color $GREEN "PostgreSQL database created"
    fi
    
    # Run database migrations
    python3 -c "from core.database import init_db; init_db()"
    print_color $GREEN "Database initialized"
}

# Configure services
configure_services() {
    print_color $GREEN "Configuring services..."
    
    # Configure Nginx
    cat > /etc/nginx/sites-available/axis << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/axis /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Configure Supervisor
    cat > /etc/supervisor/conf.d/axis.conf << EOF
[program:axis]
command=/home/$SUDO_USER/projects/axis/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/$SUDO_USER/projects/axis
user=$SUDO_USER
autostart=true
autorestart=true
stderr_logfile=/home/$SUDO_USER/projects/axis/logs/axis.err.log
stdout_logfile=/home/$SUDO_USER/projects/axis/logs/axis.out.log
EOF
    
    # Restart services
    systemctl restart nginx
    systemctl restart supervisor
    
    print_color $GREEN "Services configured"
}

# Main installation process
main() {
    print_color $GREEN "Starting Axis AI installation..."
    
    check_python
    check_cuda
    install_system_deps
    create_venv
    install_python_deps
    create_directories
    init_database
    configure_services
    
    print_color $GREEN "Installation complete!"
    print_color $GREEN "You can now access the application at http://localhost"
    print_color $YELLOW "Please update config.yaml with your settings"
}

# Run main installation
main
