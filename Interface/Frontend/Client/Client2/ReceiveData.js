document.addEventListener("DOMContentLoaded", () => {
    
    const clientId = "F2"
    const statusr = document.getElementById("status");
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${clientId}`);
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
            ws.send("B_end" +test);
            Changestatus("Clicked button: " + test);
        } else {
            Changestatus("WebSocket is not open");
        }
    }
    function sendMessageButtonb(message){
        if (ws.readyState == WebSocket.OPEN){
            ws.send(message);
            Changestatus("Send message: "+ message);
        }
    }
    function sendMessageButtonf(message){
        if (ws.readyState == WebSocket.OPEN){
            ws.send("F_end"+ message);
            Changestatus("Send message: "+ message);
        }
    }

    function Changestatus(message){
        statusr.textContent = message;;
        console.log(message)
    }

    window.sendButtonClick = sendButtonClick; 
    window.sendMessageButtonb = sendMessageButtonb; 
    window.sendMessageButtonf = sendMessageButtonf; 
});