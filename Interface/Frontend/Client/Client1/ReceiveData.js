document.addEventListener("DOMContentLoaded", () => {
    const clientId = "F1";
    const statusr = document.getElementById("status");
    const wsUrl = `ws://127.0.0.1:8000/ws/${clientId}`;
    let ws = null;
    let machinesData = [];
    let machines = []
    function connectWebSocket() {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            updateStatus(`Connected to server: ${ws.url}`);
        };
        ws.onmessage = (event) => {
            console.log("Message from server:" + event.data);
            try {
                const message = JSON.parse(event.data);
                if (message.type_message == "status") {
                    const output = document.getElementById("output");
                    output.innerHTML += `<div>${message.data}</div>`;
                    output.scrollTop= output.scrollHeight;
                } else if (message.type_message == "config") {
                    console.log("Config message received:", message.data);
                        let configText = '';
                        machinesData = [];
                        for (const key in message.data) {
                            if (message.data.hasOwnProperty(key)) {
                                machinesData.push(message.data[key]);
                                configText += `Machine ID: ${message.data[key].machine_id}, Number of PCs: ${message.data[key].numb_of_pcs} \n `;
                            }
                        }
                        generateMachineTabs(machinesData);
                        configElement.textContent = `${configText}Number of machines in total: ${machinesData.length}`;
                    } else {
                        console.error("Element with ID 'config' not found");
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

    function startCalibration(pc_id) {
        sendMessageToServer("command", "B_end_start_calibration", pc_id);
    }

    function initialize_machine() {
        sendMessageToServer("command", "B_end_initialize_machine");
    }

    function displayImage(base64String) {
        console.log("Message is a picture");
        let img = base64String;
        var image = new Image();
        image.src = `data:image/png;base64, ${img}`;
        const imgContainer = document.getElementById("imgContainer");
        imgContainer.innerHTML = "";
        imgContainer.appendChild(image);
        console.log(base64String);
    }

    function sendMessageToServer(type_message, message, data) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message: type_message, message: message, data: data }));
            updateStatus(`Sent ${type_message}: ${message} and data ${data}`);
        } else {
            updateStatus("WebSocket is not open");
        }
    }
    
    function sendStatusUpdate(type, message) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message: type, data: message }));
            updateStatus(`Sent message: ${message}`);
        } else {
            updateStatus("WebSocket is not open");
        }
    }

    function updateStatus(message) {
        const statusElement = document.getElementById("status");
        const outputElement = document.getElementById("output");
    
        statusElement.textContent = message;
    
        const newMessage = document.createElement("div");
        newMessage.textContent = message;
        outputElement.appendChild(newMessage);

        outputElement.scrollTop = outputElement.scrollHeight;
    
        console.log(message);
    }

    function generateMachineTabs(machinesData) {
        let machine_info = []
        const tabsContainer = document.getElementById("machineTabs");
        const contentContainer = document.getElementById("tabContent");
    
        tabsContainer.innerHTML = '<li class="active"><a data-toggle="tab"  style="color: #2e5426;" href="#start">Start</a></li>';
        contentContainer.innerHTML = `
            <div id="start" class="tab-pane fade in active">
                  

            <div style="border: 1px solid #ddd; padding: 10px;margin-top: 20px; width: 40%;">
            <h4>Status Frontend:</h4>
            <div id="status" class="border p-3" style="border: 1px solid #ddd; padding: 10px; width: 90%;"></div>
            </div>
            
        
            <button class="btn btn-primary m-2" onclick="initialize_machine()">Initialize again</button>
            </div>
        `;
    
        machinesData.forEach((machine, index) => {
            tabsContainer.innerHTML += `
                <li><a data-toggle="tab" style="color: #2e5426;"href="#machine${index}">${machine.name}</a></li>
            `;
    
            let pcSections = "";
            for (const pcKey in machine.pcs) {
                if (machine.pcs.hasOwnProperty(pcKey)) {
                    const pc = machine.pcs[pcKey];
                    const numCameras = pc.cameras.length;
                    let cameraImages = "";

                    pc.cameras.forEach(cameraId => {
                        cameraImages += `
                            <div style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 90%; margin-bottom: 20px;">
                                <h5>Camera ${cameraId} Image:</h5>
                                <img id="camera${cameraId}_pc${pc.pc_id}_machine${machine.machine_id}" class="img-responsive" src="" alt="Camera ${cameraId} Image">
                            </div>
                        `;
                    });
    
                    pcSections += `
                        <div class="col-md-4 pc-section" style="border:1px solid #ddd; margin-top: 20px;width: 30%; margin-right: 10px; margin-left: 10px;">
                            <h3>PC ID: ${pc.pc_id} IP: ${pc.ip}</h3>
                            <div style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 90%; margin-bottom: 20px;">
                                <h5>Number of cameras: ${numCameras}</h5>
                            </div>
                            <div style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 90%; margin-bottom: 20px;">
                                <h5>Status:</h5>
                                <div id="output" class="border p-3" style="border: 1px solid #ddd; padding: 10px; width: 100%; height: 90px; overflow-y: auto;"></div>
                            </div>
                            ${cameraImages}
                        </div>
                    `;
                }
            }
    
            contentContainer.innerHTML += `
                <div id="machine${index}" class="tab-pane fade">
                    <div id="contentBox${machine.machine_id}" class="row justify-content-center" style="margin:10px auto; width:100%; display: flex; justify-content: center;">
                        ${pcSections}
                    </div>
                    <div class="d-flex justify-content-center" style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 30%; margin: 0 auto;">
                        <div class="text-center machine-config" style="margin-top: 20px;">
                            <label for="machine_config">Machine Config:</label>
                            <select name="machine_config" id="machine_config">
                                <option value="63">63 mm</option>
                                <option value="90">90 mm</option>
                            </select>
                        </div>
                        
                        <div class="text-center" >
                            <button class="btn btn-primary m-2" onclick="startCalibration('${machine.machine_id}')">Start calibration ${machine.name}</button>
                        </div>
                    </div>
                </div>
            `;
        });
    }

    window.sendMessageToServer = sendMessageToServer;
    window.sendStatusUpdate = sendStatusUpdate;
    window.startCalibration = startCalibration;
    window.initialize_machine = initialize_machine;
    connectWebSocket();
});