document.addEventListener("DOMContentLoaded", () => {
    const clientId = "Front-end";
    const wsUrl = `ws://127.0.0.1:8000/ws/${clientId}`;
    console.log(wsUrl);
    let ws = null;
    let machinesData = [];
    let connected_pcs = [];
    let pcStatusData = {};
    let pcImageData = {};

    function connectWebSocket() {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            updateStatus(`Connected to server: ${ws.url}`);
            initialize_machine();
            initializePCStatusData();
            initializePCImageData();
            updatePCConnectionStatus();
        };

        ws.onmessage = (event) => {
            handleServerMessage(event.data);
        };

        ws.onerror = (error) => {
            updateStatus(`WebSocket error: ${error.message}`);
        };

        ws.onclose = () => {
            updateStatus("Connection closed, reconnecting in 5 seconds...");
            setTimeout(connectWebSocket, 5000);
        };
    }

    function handleServerMessage(data) {
        console.log("Message from server:" + data);
        try {
            const message = JSON.parse(data);

            switch (message.type_message) {
                case "status":
                    handleStatusMessage(message.data);
                    break;
                case "config":
                    handleConfigMessage(message.data);
                    break;
                case "connected_pcs":
                    handleConnectedPCsMessage(message.data);
                    break;
                default:
                    console.error("Unknown message type:", message.type_message);
            }
        } catch (e) {
            console.error("Error parsing message:", e);
        }
    }

    function handleStatusMessage(pc) {
        console.log(`Received status update for PC ${pc.ip}: ${pc.status}`);
        pcStatusData[pc.ip] = pc.status;
        pcImageData[pc.ip] = pc.last_images;
        updatePCStatus(pc);
        updatePCImages(pc);
        updateLastCalibration(pc);
    }

    function handleConfigMessage(data) {
        console.log("Config message received:", data);
        let configText = '';
        machinesData = [];
        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                machinesData.push(data[key]);
                configText += `Machine ID: ${data[key].machine_id}, Number of PCs: ${data[key].numb_of_pcs}\n`;
                generateMachineTabs(machinesData);
            }
        }
        const configElement = document.getElementById("configElement");
        if (configElement) {
            configElement.textContent = `${configText}Number of machines in total: ${machinesData.length}`;
        }
    }

    function handleConnectedPCsMessage(data) {
        connected_pcs = data.flat();
        console.log(connected_pcs);
        updatePCConnectionStatus();
    }

    function startCalibration(machine_id) {
        console.log(machine_id);
        sendMessageToServer("command", "start_calibration", machine_id);
    }

    function initialize_machine() {
        sendMessageToServer("command", "initialize_machine");
        updateStatus("Initializing machine...");
    }

    function sendMessageToServer(type_message, message, data) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message, message, data }));
            updateStatus(`Sent ${type_message}: ${message} and data ${data}`);
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

    function updatePCStatus(pc) {
        const statusElement = document.getElementById(`status_${pc.ip}`);
        if (statusElement) {
            statusElement.innerHTML = pc.status.map(status => `<div>${status}</div>`).join('');
            statusElement.scrollTop = statusElement.scrollHeight;
        }
    }

    function updatePCImages(pc) {
        const images = pcImageData[pc.ip];
        if (images) {
            const flattenedImages = images.flat();
            const machine_id = getMachineIdForPC(pc.ip);
            if (machine_id === null) {
                console.error(`Machine ID not found for PC ${pc.ip}`);
                return;
            }

            const cams = pc.cameras;
            cams.forEach((cameraId, i) => {
                const imageContainerId = `camera${cameraId}_pc${pc.pc_id}_machine${machine_id}`;
                const imageContainer = document.getElementById(imageContainerId);
                if (imageContainer) {
                    imageContainer.innerHTML = "";
                    const base64String = flattenedImages[i];
                    if (base64String) {
                        const dataUrl = 'data:image/jpeg;base64,' + base64String;
                        const img = document.createElement('img');
                        img.src = dataUrl;
                        img.alt = `Encoded Image ${i}`;
                        img.className = "img-responsive";
                        img.style.maxWidth = "100%";
                        img.style.maxHeight = "200px";
                        img.onclick = () => enlargeImg(img);
                        imageContainer.appendChild(img);
                        console.log(`Updated image for camera ${cameraId} on PC ${pc.ip} with ID ${imageContainerId}`);
                    } else {
                        console.error(`No base64 string found for camera ${cameraId} on PC ${pc.ip}`);
                    }
                } else {
                    console.error(`Element with ID '${imageContainerId}' not found`);
                }
            });
        } else {
            console.error(`No image data found for PC ${pc.ip}`);
        }
    }

    function getMachineIdForPC(pc_ip) {
        for (const machine of machinesData) {
            for (const pcKey in machine.pcs) {
                if (machine.pcs.hasOwnProperty(pcKey)) {
                    const machinePC = machine.pcs[pcKey];
                    if (machinePC.ip === pc_ip) {
                        return machine.machine_id;
                    }
                }
            }
        }
        return null;
    }

    function updateLastCalibration(pc) {
        const lastCalibrationElement = document.getElementById(`last_calibration${pc.pc_id}`);
        if (lastCalibrationElement) {
            const lastCalibrationArray = Array.isArray(pc.last_calibration) ? pc.last_calibration : [pc.last_calibration];
            lastCalibrationElement.innerHTML = lastCalibrationArray.map(calibration => `<div>${calibration}</div>`).join('');
            lastCalibrationElement.scrollTop = lastCalibrationElement.scrollHeight;
        } else {
            console.error(`Element with ID 'last_calibration${pc.pc_id}' not found`);
        }
    }

    function updatePCConnectionStatus() {
        machinesData.forEach(machine => {
            for (const pcKey in machine.pcs) {
                if (machine.pcs.hasOwnProperty(pcKey)) {
                    const pc = machine.pcs[pcKey];
                    const statusElement = document.getElementById(`status-container-${pc.ip}`);
                    if (statusElement) {
                        const isConnected = connected_pcs.includes(pc.ip.toString());
                        statusElement.innerHTML = `
                            <h5>Status: ${isConnected ? 'Online' : 'Offline'}</h5>
                            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: ${isConnected ? 'green' : 'red'};"></div>
                        `;
                    }
                }
            }
        });

        const allpcElement = document.getElementById("connected-clients");
        if (allpcElement) {
            allpcElement.innerHTML = connected_pcs.length > 0
                ? connected_pcs.map(ip => `<div>PC ${ip} is connected</div>`).join('')
                : `<div>No PC connected</div>`;
        }
    }

    function initializePCStatusData() {
        machinesData.forEach(machine => {
            for (const pcKey in machine.pcs) {
                if (machine.pcs.hasOwnProperty(pcKey)) {
                    const pc = machine.pcs[pcKey];
                    if (pcStatusData[pc.ip]) {
                        updatePCStatus({ ip: pc.ip, status: pcStatusData[pc.ip] });
                    }
                }
            }
        });
    }

    function initializePCImageData() {
        machinesData.forEach(machine => {
            for (const pcKey in machine.pcs) {
                if (machine.pcs.hasOwnProperty(pcKey)) {
                    const pc = machine.pcs[pcKey];
                    if (pcImageData[pc.ip]) {
                        updatePCImages({ ip: pc.ip, cameras: pc.cameras, pc_id: pc.pc_id });
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
                            <div style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 30%; margin-bottom: 20px; justify-content: center; display: flex;">
                                <img id="camera${cameraId}_pc${pc.pc_id}_machine${machine.machine_id}" class="img-responsive" src="" alt="Camera ${cameraId} Image" onclick="enlargeImg(this)">
                            </div>
                        `;
                    });

                    pcSections += `
                                <div class="col-md-4 pc-section" style="border: 1px solid #ddd; margin-top: 10px; width: 90%; margin: 0 10px;">
                <h3>PC${pc.ip}</h3>
                <div id="cntr${pc.ip}" style="border: 1px solid #ddd; padding: 10px; margin-top: 10px; width: 90%; margin-bottom: 20px;">
                    <div id="status-container-${pc.ip}">
                        <div style="display: flex; align-items: center;">
                            <h5>Status: ${connected_pcs.includes(pc.ip.toString()) ? 'Online' : 'Offline'}</h5>
                            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: ${connected_pcs.includes(pc.ip.toString()) ? 'green' : 'red'}; margin-left: 1px;"></div>
                        </div>
                    </div>
                    <h5>Number of cameras: ${numCameras}</h5>
                </div>
                <div style="border: 1px solid #ddd; padding: 10px; margin-top: 10px; width: 90%; margin-bottom: 10px;">
                    <h5>Status of PC${pc.ip}</h5>
                    <div id="status_${pc.ip}" class="border p-3" style="border: 1px solid #ddd; padding: 10px; width: 100%; height: 90px; overflow-y: auto;"></div>
                </div>
                <div id="cameraContainer_${pc.pc_id}_${machine.machine_id}_outer" style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 90%; margin-bottom: 10px;">
                    <div id="cameraContainer_${pc.pc_id}_${machine.machine_id}_inner" style="display: flex; overflow-x: auto; width: 100%; height: auto; justify-content: center;">
                        ${cameraImages}
                    </div>
                    <p>Click on the image to zoom in</p>
                </div>
                <div style="border: 1px solid #ddd; padding: 10px; margin-top: 20px; width: 90%; margin-bottom: 10px;">
                    <h5>Last calibration:</h5>
                    <div id="last_calibration${pc.pc_id}"></div>
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
    window.startCalibration = startCalibration;
    window.initialize_machine = initialize_machine;
    connectWebSocket();
});

function enlargeImg(img) {
    if (!document.fullscreenElement) {
        img.dataset.oldStyle = img.getAttribute("style") || "";
        img.style.maxWidth = "100vw";
        img.style.maxHeight = "100vh";
        img.style.width = "100vw";
        img.style.height = "100vh";
        img.style.objectFit = "contain";
        img.style.backgroundColor = "black";
        img.style.position = "fixed";
        img.style.top = "0";
        img.style.left = "0";

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

        if (img.dataset.oldStyle !== undefined) {
            setTimeout(() => {
                img.setAttribute("style", img.dataset.oldStyle);
            }, 300);
        }
    }
}