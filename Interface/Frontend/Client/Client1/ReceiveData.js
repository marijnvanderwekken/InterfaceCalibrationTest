document.addEventListener("DOMContentLoaded", () => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    const statusr = document.getElementById("status");

    ws.onopen = () => {
        Changestatus("Connected to server "+ ws.url)
    };

    ws.onmessage = (event) => {
        console.log("Message from server:" + event.data);
        const output = document.getElementById("output");
        output.textContent = event.data;
    };

    ws.onerror = (error) => {
        Changestatus("error: " + error.message);
    };

    ws.onclose = () => {
        Changestatus("connection closed");
    };

    function sendButtonClick(test){
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(test);
            Changestatus("Clicked button: " + test);
        } else {

            Changestatus("WebSocket is not open");
        }
    }

    function Changestatus(message){
        statusr.textContent = message;;
        console.log(message)
    }

    window.sendButtonClick = sendButtonClick; 
});