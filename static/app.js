// --- Global Variables and Constants ---
let currentPathLayer;

/**
 * SPLASH SCREEN LOGIC
 * This handles the smooth transition from the logo screen to the map.
 */
function hideSplashScreen() {
    const splash = document.getElementById('splash-screen');
    if (splash) {
        // Wait 3 seconds (3000ms) to show the logo
        setTimeout(() => {
            splash.style.opacity = '0';
            // After the fade animation (0.8s), hide it completely
            setTimeout(() => {
                splash.style.visibility = 'hidden';
                splash.style.display = 'none';
            }, 800);
        }, 3000);
    }
}

// --- Helper Functions ---

/**
 * Clears the previous route line.
 */
function clearMapElements() {
    if (currentPathLayer && typeof map !== 'undefined') {
        map.removeLayer(currentPathLayer);
        currentPathLayer = null;
    }
}

/**
 * Fetches the list of POIs from the Flask API.
 */
async function fetchAndPopulatePois() {
    console.log("Attempting to fetch POI data...");
    try {
        const response = await fetch('/api/pois');

        if (!response.ok) {
            console.error(`API response failed: Status ${response.status}`);
            return;
        }

        const data = await response.json();

        if (data.success && data.pois) {
            const pois = data.pois;
            const startSelect = document.getElementById('start-location-select');
            const endSelect = document.getElementById('end-location-select');

            startSelect.innerHTML = '<option value="">-- Select Start --</option>';
            endSelect.innerHTML = '<option value="">-- Select Destination --</option>';

            pois.forEach(poi => {
                const optionText = `${poi.name}`;
                const startOption = new Option(optionText, poi.name);
                startOption.dataset.id = poi.id;

                const endOption = new Option(optionText, poi.name);
                endOption.dataset.id = poi.id;

                startSelect.add(startOption);
                endSelect.add(endOption);

                if (typeof L !== 'undefined' && typeof map !== 'undefined') {
                    L.marker([poi.lat, poi.lng]).addTo(map).bindPopup(poi.name);
                }
            });
        }
    } catch (error) {
        console.error("Network Error fetching POIs:", error);
    }
}

// --- ROUTE BUTTON LOGIC ---
document.getElementById("findRoute").addEventListener("click", async () => {
    const startSelect = document.getElementById("start-location-select");
    const endSelect = document.getElementById("end-location-select");
    const algo = document.getElementById("algorithm").value;
    const accessible = document.getElementById("accessibility").checked;

    const startOption = startSelect.options[startSelect.selectedIndex];
    const endOption = endSelect.options[endSelect.selectedIndex];
    const messageBox = document.getElementById("output-message");

    if (!startOption.dataset.id || !endOption.dataset.id) {
        messageBox.innerHTML = '<div style="color: orange;">Select Start and End locations.</div>';
        return;
    }

    const startId = parseInt(startOption.dataset.id);
    const endId = parseInt(endOption.dataset.id);

    clearMapElements();
    messageBox.innerHTML = 'Calculating route...';

    try {
        const response = await fetch('/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_id: startId,
                end_id: endId,
                algorithm: algo,
                accessible: accessible,
            }),
        });

        const result = await response.json();

        if (result.success && result.path_coords && result.path_coords.length > 0) {
            drawPath(result.path_coords);
            messageBox.innerHTML = '<div style="color: green; font-weight: bold;">Route Found!</div>';
        } else {
            messageBox.innerHTML = '<div style="color: red;">No Path Found.</div>';
        }
    } catch (error) {
        messageBox.innerHTML = 'Error connecting to server.';
    }
});

// DRAW ROUTE FUNCTION
function drawPath(coordinates) {
    if (currentPathLayer) map.removeLayer(currentPathLayer);
    const latlngs = coordinates.map(coord => [coord.lat, coord.lng]);
    currentPathLayer = L.polyline(latlngs, { color: "red", weight: 6 }).addTo(map);
    map.fitBounds(currentPathLayer.getBounds(), { padding: [50, 50] });
}

// --- LECTURE SCHEDULE DATA ---
const weeklyLectureSchedule = {
    1: [
        { time: "07:30 - 08:30", subject: "BI(P)", room: "New Lab", teacher: "Ishaq Sir" },
        { time: "08:30 - 09:30", subject: "BI(P)", room: "New Lab", teacher: "Ishaq Sir" },
        { time: "09:30 - 10:30", subject: "EN", room: "Room 103", teacher: "Priyanka Miss" },
        { time: "11:00 - 12:00", subject: "IS", room: "Room 103", teacher: "Blecina Miss" }
    ],
    2: [
        { time: "07:30 - 08:30", subject: "IS(P) ", room: "New Lab", teacher: "Blecina Miss" },
        { time: "08:30 - 09:30", subject: "IS(P)", room: "New Lab", teacher: "Blecina Miss" },
        { time: "09:30 - 10:30", subject: "EN", room: "Room 103", teacher: "Priyanka Miss" },
        { time: "11:00 - 12:00", subject: "STQA", room: "Room 103", teacher: "Amruta Miss" }
    ],
    3: [
        { time: "07:30 - 08:30", subject: "EN(P)", room: "New Lab", teacher: "Priyanka Miss" },
        { time: "08:30 - 09:30", subject: "EN(P)", room: "New Lab", teacher: "Priyanka Miss" },
        { time: "09:30 - 10:30", subject: "STQA", room: "Room 103", teacher: "Amruta Miss" },
        { time: "11:00 - 12:00", subject: "BI", room: "Room 103", teacher: "Ishaq Sir" }
    ],
    4: [
        { time: "07:30 - 08:30", subject: "IT ACT", room: "Room 103", teacher: "Priyanka Miss" },
        { time: "08:30 - 09:30", subject: "BI", room: "Room 103", teacher: "Ishaq Sir" },
        { time: "09:30 - 10:30", subject: "PROJECT", room: "New Lab", teacher: "Ashok Sir" },
        { time: "11:00 - 12:00", subject: "EN", room: "Room 103", teacher: "Priyanka Miss" }
    ],
    5: [
        { time: "07:30 - 08:30", subject: "AM(P)", room: "Room 103", teacher: "Raju Sir" },
        { time: "08:30 - 09:30", subject: "AM(P)", room: "Room 103", teacher: "Raju Sir" },
        { time: "09:30 - 10:30", subject: "EN", room: "Room 103", teacher: "Priyanka Miss" },
        { time: "11:00 - 12:00", subject: "STQA", room: "Room 103", teacher: "Amruta Miss" }
    ],
    6: [
        { time: "07:30 - 08:30", subject: "EN", room: "Room 103", teacher: "Priyanka Miss" },
        { time: "08:30 - 09:30", subject: "IS", room: "Room 103", teacher: "Blecina Miss" },
        { time: "09:30 - 10:30", subject: "IT ACT", room: "New Lab", teacher: "Priyanka Miss" },
        { time: "11:00 - 12:00", subject: "BI", room: "Room 103", teacher: "Ishaq Sir" }
    ],
    0: []
};

function updateLectureStatus() {
    const now = new Date();
    const currentDay = now.getDay();
    const hr = now.getHours();
    const min = now.getMinutes();
    const timeNum = hr * 100 + min;

    const todayLectures = weeklyLectureSchedule[currentDay] || [];
    let current = "No ongoing lecture";
    let next = "No upcoming lecture";

    for (let i = 0; i < todayLectures.length; i++) {
        const lec = todayLectures[i];
        const [s, e] = lec.time.split(" - ");
        const sNum = Number(s.replace(":", ""));
        const eNum = Number(e.replace(":", ""));

        if (timeNum >= sNum && timeNum < eNum) {
            current = `CURRENT: <b>${lec.subject}</b><br>Teacher: ${lec.teacher}<br>Room: ${lec.room}`;
            next = (i + 1 < todayLectures.length) ? `NEXT: <b>${todayLectures[i+1].subject}</b>` : "No more lectures today!";
            break;
        }
        if (timeNum < sNum) {
            next = `NEXT: <b>${lec.subject}</b><br>Teacher: ${lec.teacher}`;
            break;
        }
    }
    document.getElementById("currentLecture").innerHTML = current;
    document.getElementById("nextLecture").innerHTML = next;
}

// --- EVENT DATA ---
const events = [
    { date: "2026-02-13", name: "Coding Hackathon", place: "Auditorium" },
    { date: "2026-02-13", name: "Tech Expo", place: "Ground Hall" }
];

function updateEvents() {
    const today = new Date().toISOString().split("T")[0];
    let todayEvent = "No major events today.";
    let upcomingEvent = "Upcoming Event: MRIDANG";

    events.forEach((ev) => {
        if (ev.date === today) todayEvent = `TODAY: <b>${ev.name}</b> at ${ev.place}`;
    });

    const future = events.filter(ev => ev.date > today).sort((a,b) => a.date.localeCompare(b.date));
    if (future.length > 0) upcomingEvent = `UPCOMING: <b>${future[0].name}</b> at ${future[0].place}`;

    document.getElementById("todayEvent").innerHTML = todayEvent;
    document.getElementById("upcomingEvent").innerHTML = upcomingEvent;
}

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    fetchAndPopulatePois();
    updateLectureStatus();
    updateEvents();

    // CALL THE SPLASH SCREEN REMOVAL
    hideSplashScreen();

    setInterval(updateLectureStatus, 60000);
    setInterval(updateEvents, 3600000);
});