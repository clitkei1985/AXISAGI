# AXIS AI - Advanced Collaborative AI System

![AXIS AI Logo](https://img.shields.io/badge/AXIS-AI-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

A sophisticated AI assistant built around **CodeLlama-13b-hf** with advanced memory, multi-agent collaboration, and continuous learning capabilities. AXIS AI provides offline-first AI interactions with comprehensive feature set including voice processing, image analysis, web search, and more.

## 🌟 Key Features

### Core AI Capabilities (Features 72-98)
- **CodeLlama-13b-hf** as base model with GPU optimization
- **Multi-agent collaboration** with specialized agents (coder, researcher, analyst, creative)
- **Continuous learning** from user interactions
- **Fine-tuning** with LoRA adapters for efficiency
- **Self-debugging** and error correction mechanisms

### Memory System (Features 1-35)
- **Advanced memory management** with FAISS vector search
- **Cross-session memory** persistence
- **Memory tagging** and importance scoring
- **Nonlinear memory** associations
- **Encrypted storage** for privacy

### Voice & Audio (Features 138-154, 199)
- **Real-time speech recognition** with Whisper
- **Text-to-speech** with emotion adaptation
- **Voice emotion detection** and tone adjustment
- **Low-latency processing** (<300ms)
- **Audio analysis** (BPM, chord extraction, music analysis)

### Web Interface (Features 36-55)
- **Modern web UI** with dark theme
- **Integrated code editor** with syntax highlighting
- **Chain-of-thought** reasoning visualization
- **File upload** and processing
- **Real-time collaboration** features

### Multi-Modal Processing
- **Image analysis** with YOLO object detection
- **Image generation** with Stable Diffusion
- **Audio processing** and analysis
- **Document processing** (PDF, Word, etc.)

### Advanced Features
- **Plugin system** with marketplace
- **Web search** and content extraction
- **Code analysis** and generation
- **Performance monitoring** with GPU tracking
- **Security** with encryption and audit trails

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- CUDA-compatible GPU (recommended: 16GB+ VRAM)
- 50GB+ free disk space
- 16GB+ RAM

### 1. Clone the Repository
```bash
git clone <repository-url>
cd axis
```

### 2. Run Setup (Automatic)
```bash
# This will download models, install dependencies, and configure everything
python setup_codellama.py
```

### 3. Start the System
```bash
# Use the startup script
./start_axis.sh

# Or run directly
python main.py
```

### 4. Access the Interface
Open your browser to `http://localhost:8000`

## 📋 Manual Setup

If you prefer manual setup or encounter issues:

### 1. Create Virtual Environment
```bash
python -m venv axis_env
source axis_env/bin/activate  # Linux/Mac
# axis_env\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

### 4. Download Models
```bash
# The system will prompt for HuggingFace authentication if needed
python -c "
from huggingface_hub import snapshot_download
snapshot_download('meta-llama/CodeLlama-13b-hf', local_dir='models/CodeLlama-13b-hf')
snapshot_download('meta-llama/CodeLlama-13b-Instruct-hf', local_dir='models/CodeLlama-13b-Instruct-hf')
snapshot_download('meta-llama/CodeLlama-13b-Python-hf', local_dir='models/CodeLlama-13b-Python-hf')
"
```

### 5. Initialize Database
```bash
python -c "
from core.database import init_db
import asyncio
asyncio.run(init_db())
"
```

## 🎯 Usage Examples

### Basic Chat
```python
from modules.llm_engine.local_llm import get_codellama_engine
from core.database import get_db

db = next(get_db())
engine = get_codellama_engine(db, memory_manager)

response = await engine.generate_response(
    "Write a Python function to calculate fibonacci numbers",
    agent_type="coder"
)
```

### Multi-Agent Collaboration
```python
from modules.llm_engine.agents import get_multi_agent_system

mas = get_multi_agent_system(db, memory_manager, codellama_engine)

result = await mas.process_collaborative_request(
    "Analyze this dataset and create a machine learning model",
    user=current_user,
    use_chain_of_thought=True
)
```

### Voice Interaction
```python
from modules.audio_voice.voice_engine import get_voice_engine

voice = get_voice_engine(db)
await voice.start_real_time_processing()

# Speech to text
text, confidence = await voice.recognize_speech()

# Text to speech with emotion
audio = await voice.synthesize_speech(
    "Hello! How can I help you today?",
    emotion="happy"
)
```

## 🛠️ Configuration

### Environment Variables
```bash
# Core settings
DATABASE_URL=sqlite:///./db/axis.db
SECRET_KEY=your-secret-key

# Model paths
MODELS_DIR=./models
LOCAL_MODEL_PATH=./models/CodeLlama-13b-hf

# API Keys (optional)
OPENAI_API_KEY=sk-...
HUGGINGFACE_TOKEN=hf_...

# Hardware settings
CUDA_ENABLED=true
GPU_MEMORY_FRACTION=0.8
```

### config.yaml Customization
See `config.yaml` for comprehensive configuration options including:
- Model selection and parameters
- Memory settings and retention
- Voice processing preferences
- Security and privacy settings
- Performance optimizations

## 🏗️ Architecture

### Core Components
- **LLM Engine**: CodeLlama-13b-hf integration with LoRA fine-tuning
- **Memory Manager**: FAISS-based vector storage with SQL metadata
- **Multi-Agent System**: Coordinated specialist agents
- **Voice Engine**: Real-time audio processing
- **Web Interface**: FastAPI + modern frontend
- **Plugin System**: Extensible architecture

### Data Flow
```
User Input → Web Interface → LLM Engine → Multi-Agent System
     ↓              ↓              ↓              ↓
Memory Storage ← Response ← Agent Coordination ← Specialized Processing
```

## 🔧 Development

### Adding New Features
1. Create feature module in `modules/`
2. Update `config.yaml` with settings
3. Add routes in `interfaces/`
4. Update frontend if needed

### Custom Agents
```python
from modules.llm_engine.agents import AgentRole, MultiAgentSystem

# Define new agent role
class CustomAgent(AgentRole):
    SPECIALIST = "specialist"

# Configure in agent system
agent_configs[AgentRole.SPECIALIST] = {
    "model": "meta-llama/CodeLlama-13b-hf",
    "system_prompt": "You are a specialist in...",
    "temperature": 0.5,
    "max_tokens": 2048
}
```

### Plugin Development
```python
from core.plugin_manager import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__("my_plugin", "1.0.0")
    
    async def process(self, data):
        # Plugin logic here
        return processed_data
```

## 📊 Performance

### System Requirements
- **Minimum**: 8GB GPU, 16GB RAM, 25GB storage
- **Recommended**: 16GB+ GPU, 32GB+ RAM, 100GB+ storage
- **Optimal**: RTX 4090/A100, 64GB+ RAM, NVMe SSD

### Optimization Tips
- Use GPU acceleration for best performance
- Enable quantization for memory efficiency
- Configure batch sizes based on available VRAM
- Use SSD storage for model and vector databases

## 🔒 Security & Privacy

### Data Protection
- All sensitive data encrypted at rest
- Memory can be configured for different privacy levels
- Audit trails for all admin actions
- Secure authentication with JWT tokens

### Privacy Zones
- **Private**: User-only access
- **Shared**: Controlled sharing
- **Public**: Community features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## 📖 Documentation

- **API Documentation**: Available at `/docs` when running
- **Feature Documentation**: See `FEATURE_STATUS_REPORT.md`
- **Development Guide**: See `docs/development.md`

## ⚠️ Troubleshooting

### Common Issues

**GPU Out of Memory**
```bash
# Reduce batch size in config.yaml
performance:
  batch_size: 16  # Reduce from 32
```

**Model Download Fails**
```bash
# Set HuggingFace token
export HUGGINGFACE_TOKEN=hf_your_token_here
```

**Voice Recognition Not Working**
```bash
# Install audio dependencies
sudo apt-get install portaudio19-dev  # Linux
# brew install portaudio               # macOS
```

### Getting Help
- Check the logs in `logs/axis.log`
- Review configuration in `config.yaml`
- Run diagnostics: `python test_startup.py`

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Meta AI** for CodeLlama models
- **Hugging Face** for transformers library
- **OpenAI** for Whisper and fallback capabilities
- **FastAPI** for the web framework
- **FAISS** for vector search capabilities

---

**Built with ❤️ for the AI community**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/your-repo/axis-ai).
