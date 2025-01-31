# Interface for Calibration


## Getting Started

### Prerequisites

- Python 3.x
- FastAPI
- Uvicorn
- Websockets
- Websockets-client

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/marijnvanderwekken/InterfaceCalibrationTest.git
    cd InterfaceCalibrationTest
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

### Running the Server


1. Run the FastAPI server:
    ```sh
    python3 Interface/Backend/Server/main.py
    ```

### Running the Frontend Client

1. Open `index.html` in your web browser:
    ```sh
    open Client/Client1/index.html
    ```

2. Refresh the page if you restart the server scripts to reconnect with the WebSocket.

### Running the Backend Client

1. Run the Client.py:
    ```sh
    python3 Interface/Backend/Client/Client.py
    ```

2. It will automatically reconnect when the WebSocket server is not running.



