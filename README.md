# Space Triage: AI-Guided Ultrasound Assistant

Space Triage is an AI-powered medical assistant designed for space missions, helping astronauts perform and interpret ultrasound scans with real-time guidance.

## Features

- **Welcome Page**: User-friendly interface with login functionality
- **Health Records Dashboard**: Comprehensive view of organ health status
- **Organ Selection**: Interactive interface for selecting target organs
- **AI-Guided Ultrasound**: Real-time assistance for ultrasound scanning
- **Diagnosis Support**: AI-powered analysis and recommendations

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/zulalakarsu/space.git
cd space
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

## Project Structure

- `streamlit_app.py`: Main application file
- `requirements.txt`: Python package dependencies
- `assets/`: Directory for static assets (images, etc.)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
