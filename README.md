# InterfaceCalibrationTest


## Getting Started

### Prerequisites

- Python 3.x
- FastAPI
- Uvicorn

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/InterfaceCalibrationTest.git
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
    python3 Interface/Backend/FastApi/Server.py
    ```

2. Alternatively, you can run the WebSocket server:
    ```sh
    python3 Backend/Websocket/Server.py
    ```

**Note:** Do not run both servers at the same time.

### Running the Frontend

1. Open `index.html` in your web browser:
    ```sh
    open Client/Client1/index.html
    ```

2. Refresh the page if you restart the server scripts to reconnect with the WebSocket.

### Modifying the JSON

1. To modify the JSON file, run the [TestCalibrationScript.py](http://_vscodecontentref_/2) script:
    ```sh
    python3 TestCalibrationScript.py
    ```

