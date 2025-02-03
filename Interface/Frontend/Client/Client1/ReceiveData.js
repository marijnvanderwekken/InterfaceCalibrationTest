document.addEventListener("DOMContentLoaded", () => {
    const clientId = "F1";
    const statusr = document.getElementById("status");
    const wsUrl = `ws://127.0.0.1:8000/ws/${clientId}`;
    let ws = null;
    let machine_config = '{ "machine" : [' +
    '{ "main_ip":"1.1.1.1" , "machine_config":"90", "number_of_pcs":"5" },]}';

    function connectWebSocket() {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            updateStatus(`Connected to server: ${ws.url}`);
        };

        ws.onmessage = (event) => {
            console.log("Message from server:" + event.data);
            try {
                const message = JSON.parse(event.data);
                if (message.type_message === "picture") {
                    displayImage(message.data)
                }else if(message.type_message == "status"){
                    const output = document.getElementById("output");
                    output.textContent = message.data;
                }
            } catch (e) {
                console.error("Error parsing message:", e);
            }
        };

        ws.onerror = (error) => {
            updateStatus(`WebSocket error: ${error.message}`);
        };

        ws.onclose = () => {
            updateStatus("Connection closed, reconnecting in 5 seconds...");
            setTimeout(connectWebSocket, 5000);
        };
    }
    function startCalibration() {
        const mainIp = document.getElementById("main_ip").value;
        const numMachines = document.getElementById("number_of_pcs").value;
        const machineConfig = document.getElementById("machine_config").value;

        if (isValidIP(mainIp)) {
            const machineConfigData = {
                main_ip: mainIp,
                number_of_pcs: numMachines,
                machine_config: machineConfig
            };

            //sendMessageToServer("command", "B_end_set_machine_config", JSON.stringify(machineConfigData));
            sendMessageToServer("command", "B_end_start_calibration", JSON.stringify(machineConfigData));

            document.getElementById("machine_config").selectedIndex = 0;
            document.getElementById("main_ip").value = "";
            document.getElementById("number_of_pcs").value = "";
            console.log("Calibration started and inputs reset.");
        } else {
            window.alert("IP is not valid");
        }
    }

        
        
    
    const isValidIP = (ip) => {
        const ipv4Pattern = /^(25[0-5]|2[0-4]\d|1\d{2}|\d{1,2})(\.(25[0-5]|2[0-4]\d|1\d{2}|\d{1,2})){3}$/;
        if (ipv4Pattern.test(ip)) {
            return true;
        }
    
        return false;
    };


    function displayImage(base64String) {
        console.log("Message is a picture")
            let img = base64String
            var image = new Image();
            image.src = `data:image/png;base64, ${img}`;
            const imgContainer = document.getElementById("imgContainer");
            imgContainer.innerHTML = "";
            imgContainer.appendChild(image);
            console.log(base64String)
    }

    function sendMessageToServer(type_message ,message,data) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message: type_message, message: message, data:data }));
            updateStatus(`Sent ${type_message}: ${message} and data ${data}`);
        } else {
            updateStatus("WebSocket is not open");
        }
    }

    function sendStatusUpdate(type, message) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message: type, data: message}));
            updateStatus(`Sent message: ${message}`);
        } else {
            updateStatus("WebSocket is not open");
        }
    }
   

    function updateStatus(message) {
        statusr.textContent = message;
        console.log(message);
    }


    window.sendMessageToServer = sendMessageToServer;
    window.sendStatusUpdate = sendStatusUpdate;
    window.startCalibration = startCalibration;
    connectWebSocket(); 
});
