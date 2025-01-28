const timerElement = document.getElementById('timer');
const messageDisplay = document.getElementById('message-display');
const preferenceForm = document.getElementById('preference-form');
const startStopButton = document.getElementById('start-stop-button');
const voiceSelect = document.getElementById('voice-select');
const countdownDisplay = document.getElementById('countdown');

let startTime;
let timerInterval;
let timerRunning = false;
let availableMessages ="";
let useClientSideSpeech = false; // Flag to toggle between client-side and server-side audio

if (!useClientSideSpeech) {
  const voiceContainer = document.getElementById('voice-select-id');
    voiceContainer.classList.add('hidden');
}

function startTimer() {
  startTime = new Date();
  timerInterval = setInterval(updateTimer, 1000);
  timerRunning = true;
}

function stopTimer() {
  clearInterval(timerInterval);
  timerRunning = false;
}

function updateTimer() {
  const currentTime = new Date();
  const elapsed = new Date(currentTime - startTime);
  const hours = elapsed.getUTCHours().toString().padStart(2, '0');
  const minutes = elapsed.getUTCMinutes().toString().padStart(2, '0');
  const seconds = elapsed.getUTCSeconds().toString().padStart(2, '0');
  timerElement.textContent = `${hours}:${minutes}:${seconds}`;
}

function getRandomInterval(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

function populateVoiceOptions() {
  const voices = speechSynthesis.getVoices();
  const preferredVoices = {
    'Chrome': {
      'male': 'Google UK English Male',
      'female': 'Google US English'
    },
    'Firefox': {
      'male': 'Microsoft David Desktop - English (United States)',
      'female': 'Microsoft Zira Desktop - English (United States)'
    },
    'Edge': {
      'male': 'Google UK English Male',
      'female': 'Google US English'
    },
    'Safari': {
      'male': 'Daniel',
      'female': 'Samantha'
    }
  };

  const userAgent = navigator.userAgent;
  let browser = 'Unknown';

  if (userAgent.includes('Chrome')) {
    browser = 'Chrome';
  } else if (userAgent.includes('Firefox')) {
    browser = 'Firefox';
  } else if (userAgent.includes('Edg')) {
    browser = 'Edge';
  } else if (userAgent.includes('Safari')) {
    browser = 'Safari';
  }

  const voiceOptions = preferredVoices[browser];
  let hasOtherVoices = false;

  if (voiceOptions) {
    for (const gender in voiceOptions) {
      const voiceName = voiceOptions[gender];
      const voice = voices.find(v => v.name === voiceName);
      if (voice) {
        hasOtherVoices = true;
        const option = document.createElement('option');
        option.value = voice.name;
        option.textContent = voice.name + ' (' + gender + ')';
        voiceSelect.appendChild(option);
      }
    }
  }

  // Show/hide the "no voices" message
  const noVoicesMessage = document.getElementById('no-voices-message');
  if (hasOtherVoices) {
    noVoicesMessage.classList.add('hidden');
  } else {
    noVoicesMessage.classList.remove('hidden');
  }
}

// Call populateVoiceOptions initially
populateVoiceOptions();

// Add event listener for voiceschanged
speechSynthesis.onvoiceschanged = populateVoiceOptions;

function showMotivation() {
  if (availableMessages.length === 0) {
    // Get the spiciness and heroes from the form
    const spiciness = document.querySelector('select[name="motivation_style"]').value;
    const heroes = document.querySelector('input[name="heroes"]').value;

    messageDisplay.textContent = `Generating ${spiciness} ${heroes ? heroes + ' ' : ''}messages...`;

    fetch('/process_form', {
        method: 'POST',
        body: new FormData(preferenceForm)
      })
      .then(response => response.json())
      .then(data => {
        availableMessages = data.message;
        availableAudioUrls = data.audiourl;
        console.log(data)
        showMotivation();
      });
  } else {
    const randomIndex = Math.floor(Math.random() * availableMessages.length);
    const randomMessage = availableMessages.splice(randomIndex, 1)[0];
    const randomAudioUrl = availableAudioUrls.splice(randomIndex,1)[0];

    messageDisplay.textContent = randomMessage;

    if (useClientSideSpeech) {
      // Use client-side speech synthesis
      const utterance = new SpeechSynthesisUtterance(randomMessage);
      const selectedVoiceName = voiceSelect.value;
      const selectedVoice = speechSynthesis.getVoices().find(voice => voice.name === selectedVoiceName);
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
      speechSynthesis.speak(utterance);
    } else {
      // Use server-side audio 
      const audio = new Audio(randomAudioUrl);
      audio.play();
    }

    if (timerRunning) {
      let countdown = getRandomInterval(5, 30);
      countdownDisplay.textContent = `Next message in ${countdown} seconds...`;

      const countdownInterval = setInterval(() => {
        countdown--;
        countdownDisplay.textContent = `Next message in ${countdown} seconds...`;

        if (countdown <= 0) {
          clearInterval(countdownInterval);
          showMotivation();
        }
      }, 1000);
    }
  }
}

startStopButton.addEventListener('click', (event) => {
  event.preventDefault();

  if (!timerRunning) {
    startTimer();
    showMotivation();
    startStopButton.textContent = "Stop Workout";

    const settingsContainer = document.getElementById('settings-container');
    settingsContainer.classList.add('hidden');
  } else {
    stopTimer();
    startStopButton.textContent = "Start Workout!";

    const settingsContainer = document.getElementById('settings-container');
    settingsContainer.classList.remove('hidden');

  }
});