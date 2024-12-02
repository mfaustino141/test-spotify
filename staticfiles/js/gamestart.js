let startupValue = '';
var startupID = '';

var newPage = false; 

var button = document.getElementById('button');
var select = document.getElementById('select');
var textarea = document.querySelector('textarea');

var chosen = false; 

async function validateSpotifyID(id, type) {
    const endpoint = `/api/validate-spotify-id/${type}/${id}/`;

    try {
        const response = await fetch(endpoint);
        const data = await response.json();

        if (response.ok) {
            if (data.valid) {
                console.log(`${type} ID is valid:`, id);
                return true;
            } else {
                console.warn(`${type} ID is invalid:`, id);
                return false;
            }
        } else {
            console.error(`Error validating ${type} ID:`, data.error);
            return false;
        }
    } catch (error) {
        console.error('An error occurred while validating the Spotify ID:', error);
        return false;
    }
}

button.addEventListener("click", async function() {
    if(!newPage) {
        startupValue = parseInt(select.value); 
        startupID = textarea.value; 

        if(startupValue == 0){
            showShortNotification("You have to pick a preference!")
            return;
        }

        let isValid = false;

        if (startupValue === 8 || startupValue === 9) {
            isValid = true;
        } else if (startupValue === 1 || startupValue === 3 || startupValue === 5){
            const url = `/get_tracks/${getSearchType(startupValue)}/${encodeURIComponent(startupID)}/`;
            console.log('CHECKING TRACKS');
            try {
                const response = await fetch(url);
                const data = await response.json();
        
                if (data.tracks.length == 0) {
                    showShortNotification("No valid songs found! Please enter a different search.");
                    return;
                }else{
                    isValid = true;
                }
            }catch(error){
                console.error('Request failed', error);
                window.location.href = "/game/";
                return;
            } 
        }else if(startupValue > 0 && startupID.length > 0) {
            isValid = await validateSpotifyID(startupID, getTypeForValidation(startupValue));
        }

        if (isValid) {
            newPage = true; 
    
            localStorage.setItem("value", startupValue);
            localStorage.setItem("id", startupID);
            
            window.location.href = "/game/";
        } else {
            showShortNotification("Invalid ID! Please enter a different one.")
        }
    }
});

function getSearchType(value) {
    switch (value) {
        case 1: // By Artist (ID)
            return 'artist';
        case 3: // By Playlist (ID)
            return 'playlist';
        case 5: // By Album (ID)
            return 'album';
        default:
            return ''; // In case of invalid selection
    }
}

function getTypeForValidation(value) {
    switch (value) {
        case 2: // By Artist (ID)
            return 'artist';
        case 4: // By Playlist (ID)
            return 'playlist';
        case 6: // By Album (ID)
            return 'album';
        case 7: // By Track (ID)
            return 'track';
        default:
            return ''; // In case of invalid selection
    }
}

select.addEventListener("change", function() {
    if(!newPage) {
        if(!chosen) {
            select.style.color = "#ddd";
            chosen = true;
        }

        textarea.value = "";
        textarea.disabled = false; 

        if(select.value == 1) {
            textarea.placeholder = "Enter artist by name";
        } else if(select.value == 2) {
            textarea.placeholder = "Enter artist by id"; 
        } else if(select.value == 3) {
            textarea.placeholder = "Enter the playlist name";
        } else if(select.value == 4) {
            textarea.placeholder = "Enter the playlist id";
        } else if(select.value == 5) {
            textarea.placeholder = "Enter the album name";
        } else if(select.value == 6) {
            textarea.placeholder = "Enter the album id";
        } else if(select.value == 7) {
            textarea.placeholder = "Enter the track id";
        } else {
            textarea.placeholder = "";
            textarea.disabled = true; 
        }
    }
})

function showShortNotification(message) {
    console.log("SHOWING SHORT NOTIFICATION")
    const shortNotification = document.getElementById('short-notification');
    const messageElement = document.getElementById('short-notification-message');
    messageElement.textContent = message;
    shortNotification.classList.remove('hidden');

    setTimeout(() => {
        shortNotification.classList.add('hidden');
        console.log("CLOSING SHORT NOTIFICATION")
    }, 3000);
}

textarea.addEventListener('keydown', function(e) {
    if(e.key == "Enter") {
        e.preventDefault();
        button.click();
    }
})
