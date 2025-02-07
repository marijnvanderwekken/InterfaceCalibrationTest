document.addEventListener("DOMContentLoaded", () => {
    const clientId = "Front-end";
    const statusr = document.getElementById("status");
    const wsUrl = `ws://192.168.1.90:8000/ws/${clientId}`;
    let ws = null;
    let machinesData = [];
    let machines = [];
    let current_client = "";
    let current_status = [[]];
    let connected_pcs = []

    function connectWebSocket() {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            updateStatus(`Connected to server: ${ws.url}`);
            initialize_machine();
        };

        ws.onmessage = (event) => {
            console.log("Message from server:" + event.data);
            try {
                const message = JSON.parse(event.data);

                if (message.type_message === "status") {
                    const current_client = message.client;
                    if (!current_status[current_client]) {
                        current_status[current_client] = [];
                    }
                    current_status[current_client].push(message.data);
                    const output = document.getElementById(`status_${current_client}`);
                    console.log(`Received from client ${current_client}`);

                    output.innerHTML += `<div>${message.data}</div>`;
                    output.scrollTop = output.scrollHeight;

                } else if (message.type_message === "config") {
                    console.log("Config message received:", message.data);
                    let configText = '';
                    machinesData = [];
                    for (const key in message.data) {
                        if (message.data.hasOwnProperty(key)) {
                            machinesData.push(message.data[key]);
                            configText += `Machine ID: ${message.data[key].machine_id}, Number of PCs: ${message.data[key].numb_of_pcs}\n`;
                        }
                    }
                    
                    generateMachineTabs(machinesData);
                    const configElement = document.getElementById("configElement");
                    if (configElement) {
                        configElement.textContent = `${configText}Number of machines in total: ${machinesData.length}`;
                    }

                } else if (message.message === "W_send_cam_image") {
                    console.log("Image message received from client", message.client);
                    console.log("Check machinedata", machinesData);

                    const current_client_ip = message.client;
                    let machine_id = null;
                    let pc_id = null;
                    let cams = [];
                    let imagedata = [];

                    for (const machine of machinesData) {
                        for (const pcKey in machine.pcs) {
                            if (machine.pcs.hasOwnProperty(pcKey)) {
                                const pc = machine.pcs[pcKey];
                                if (pc.ip == current_client_ip) {
                                    console.log(pc.ip);
                                    cams = pc.cameras;
                                    machine_id = machine.machine_id;
                                    pc_id = pc.pc_id;
                                    break;
                                }
                            }
                        }
                        if (machine_id !== null) break;
                    }

                    console.log("Found machineid", machine_id);
                    console.log("Numbers of cameras:", cams.length);
                    console.log('Message data', message.data);

                    if (Array.isArray(message.data)) {
                        imagedata = message.data.map((base64String, index) => {
                            return { cameraId: cams[index], base64String };
                        });

                        for (let i = 0; i < cams.length; i++) {
                            const imageElement = document.getElementById(`camera${cams[i]}_pc${pc_id}_machine${machine_id}`);
                            if (imageElement) {
                                imageElement.src = `data:image/png;base64,${imagedata[i].base64String}`;
                                console.log(`Updated image for camera ${cams[i]} on PC ${pc_id} of machine ${machine_id}`);
                            } else {
                                console.error(`Element with ID 'camera${cams[i]}_pc${pc_id}_machine${machine_id}' not found`);
                            }
                        }
                    } else {
                        console.error("message.data is not an array of base64 strings");
                    }
                } else if (message.type_message === "connected_pcs") {
                    connected_pcs = message.data.flat();
                    console.log(connected_pcs);
                    updatePCStatus();
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
        updateStatus("Initializing machine...");
        generateMachineTabs(machinesData);
    }

    function displayImage(base64String) {
        console.log("Message is a picture");
        const image = new Image();
        image.src = `data:image/png;base64, ${base64String}`;
        const imgContainer = document.getElementById("imgContainer");
        imgContainer.innerHTML = "";
        imgContainer.appendChild(image);
        console.log(base64String);
    }

    function sendMessageToServer(type_message, message, data) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message, message, data }));
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

    function updatePCStatus() {
        machinesData.forEach(machine => {
            for (const pcKey in machine.pcs) {
                if (machine.pcs.hasOwnProperty(pcKey)) {
                    const pc = machine.pcs[pcKey];
                    const statusElement = document.getElementById(`status-container-${pc.ip}`);
                    if (statusElement) {
                        statusElement.innerHTML = `<h5>Status: ${connected_pcs.includes(pc.ip.toString()) ? 'Online' : 'Offline'}</h5>`;
                    }
                }
            }
        });
    }

    function generateMachineTabs(machinesData) {
        const tabsContainer = document.getElementById("machineTabs");
        const contentContainer = document.getElementById("tabContent");

        tabsContainer.innerHTML = `
        <li class="active"><a data-toggle="tab" style="color: #2e5426;" href="#start">Start</a></li>
        <li><a data-toggle="tab" style="color: #2e5426;" href="#calibrations">Calibrations</a></li>
    `;

        machinesData.forEach((machine, index) => {
            tabsContainer.innerHTML += `
                <li><a data-toggle="tab" style="color: #2e5426;" href="#machine${index}">${machine.name}</a></li>
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
                                <img id="camera${cameraId}_pc${pc.pc_id}_machine${machine.machine_id}" class="img-responsive" src="" alt="Camera ${cameraId} Image" onclick="enlargeImg(camera${cameraId}_pc${pc.pc_id}_machine${machine.machine_id})">
                            </div>
                        `;
                    });

                    pcSections += `
                        <div class="col-md-4 pc-section" style="border: 1px solid #ddd; margin-top: 10px; width: 40%; margin: 0 10px;">
                            <h3>PC${pc.ip}</h3>
                            <div id="cntr${pc.ip}" style="border: 1px solid #ddd; padding: 10px; margin-top: 10px; width: 90%; margin-bottom: 20px;">
                            <div id="status-container-${pc.ip}">
                                <h5>Status: ${connected_pcs.includes(pc.ip.toString()) ? 'Online' : 'Offline'}</h5>
                                </div>
                                <h5>Number of cameras: ${numCameras}</h5>
                            </div>
                            <div style="border: 1px solid #ddd; padding: 10px; margin-top: 10px; width: 90%; margin-bottom: 10px;">
                                <h5>Status of PC${pc.ip}</h5>
                                <div id="status_${pc.ip}" class="border p-3" style="border: 1px solid #ddd; padding: 10px; width: 100%; height: 90px; overflow-y: auto;"></div>
                            </div>
                            <div style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 90%; margin-bottom: 10px;">
                                <div id="cameraContainer_${pc.pc_id}_${machine.machine_id}" style="display: flex; overflow-x: auto; width: 100%;">
                                    ${cameraImages}
                                </div>
                                <p>Click on the image to zoom in</p>
                            </div>
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
                        <div class="text-center">
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

function enlargeImg(img) {
    if (!document.fullscreenElement) {
        if (img.requestFullscreen) {
            img.requestFullscreen();
        } else if (img.mozRequestFullScreen) {
            img.mozRequestFullScreen();
        } else if (img.webkitRequestFullscreen) {
            img.webkitRequestFullscreen();
        } else if (img.msRequestFullscreen) {
            img.msRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
}