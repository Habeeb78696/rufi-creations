let userInfo = {
  name: "", email: "", phone: "", urgency: "", service: ""
};
let currentStep = null;

const urgencyOptions = ["Immediately", "In a week", "Not urgent"];
const serviceOptions = [
  "Interior Design", "Home Décor", "Home Theatre Setup",
  "Acoustic & Soundproofing Work", "Modular Kitchen & Wardrobes",
  "Custom Furniture & Units", "Wall Paneling & Wallpaper",
  "Office & Commercial Interiors"
];

// Toggle popup on chatbot icon click
document.getElementById('chatbot-toggle-btn').addEventListener('click', () => {
  const popup = document.getElementById('chatbot-popup');
  popup.classList.toggle('active');
  if (popup.classList.contains('active')) {
    document.getElementById('chat-messages').innerHTML = '';
    displayWelcomeMessage();
  }
});

// Close chatbot popup
document.getElementById('close-btn').addEventListener('click', () => {
  document.getElementById('chatbot-popup').classList.remove('active');
});

// Send message button and enter key listener
document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keydown', function (e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendMessage();
  }
});

// Initial welcome and first prompt
function displayWelcomeMessage() {
  appendMessage('bot', '👋 Welcome to Rufi Creations! How may I assist you today?');
  setTimeout(() => {
    appendMessage('bot', 'May I know your name?');
    currentStep = 'name';
    document.getElementById('user-input').placeholder = 'Type your name...';
  }, 700);
}

// Send and handle user input
function sendMessage() {
  const userInput = document.getElementById('user-input').value.trim();
  if (userInput !== '') {
    appendMessage('user', userInput);
    handleUserInput(userInput);
    document.getElementById('user-input').value = '';
  }
}

// Display plain message
function appendMessage(sender, text) {
  const chatContainer = document.getElementById('chat-messages');
  const msg = document.createElement('div');
  msg.className = 'message ' + sender;
  msg.innerText = text;
  chatContainer.appendChild(msg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  document.getElementById('user-input').focus();
}

// Display message with clickable button options
function appendMessageWithButtons(sender, text, options) {
  document.querySelectorAll('.button-group').forEach(btn => btn.remove());
  appendMessage(sender, text);
  const chatContainer = document.getElementById('chat-messages');
  const btnGroup = document.createElement('div');
  btnGroup.className = 'button-group';
  options.forEach(option => {
    const btn = document.createElement('button');
    btn.innerText = option;
    btn.onclick = () => {
      appendMessage('user', option);
      handleUserInput(option);
      btnGroup.remove();
    };
    btnGroup.appendChild(btn);
  });
  chatContainer.appendChild(btnGroup);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Chatbot funnel step logic
function handleUserInput(userInput) {
  const lowerInput = userInput.toLowerCase();

  if (currentStep === 'name') {
    if (userInput.length >= 4) {
      userInfo.name = userInput;
      currentStep = 'email';
      appendMessage('bot', 'Thanks! May I know your email?');
    } else {
      appendMessage('bot', 'Please enter at least 4 characters for your name.');
    }

  } else if (currentStep === 'email') {
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userInput)) {
      userInfo.email = userInput;
      currentStep = 'phone';
      appendMessage('bot', 'Thanks! May I know your contact number?');
    } else {
      appendMessage('bot', 'Please enter a valid email address.');
    }

  } else if (currentStep === 'phone') {
    if (/^\d{7,13}$/.test(userInput)) {
      userInfo.phone = userInput;
      currentStep = 'urgency';
      appendMessageWithButtons('bot', 'How soon do you need our service?', urgencyOptions);
    } else {
      appendMessage('bot', 'Please enter a valid phone number (7–13 digits).');
    }

  } else if (currentStep === 'urgency') {
    const matched = urgencyOptions.find(opt => opt.toLowerCase() === lowerInput);
    if (matched) {
      userInfo.urgency = matched;
      currentStep = 'service';
      appendMessageWithButtons('bot', 'Which service are you looking for?', serviceOptions);
    } else {
      fallbackMessage();
    }

  } else if (currentStep === 'service') {
    const matched = serviceOptions.find(opt => opt.toLowerCase() === lowerInput);
    if (matched) {
      userInfo.service = matched;
      currentStep = 'confirm';
      appendMessage('bot',
        `✅ Here's what you've provided:\n👤 Name: ${userInfo.name}\n📧 Email: ${userInfo.email}\n📞 Phone: ${userInfo.phone}\n⚡ Urgency: ${userInfo.urgency}\n🛠️ Service: ${userInfo.service}`
      );
      appendMessageWithButtons('bot', 'Is everything correct?', ['Yes', 'No']);
    } else {
      fallbackMessage();
    }

  } else if (currentStep === 'confirm') {
    if (lowerInput === 'yes') {
      sendLeadToTelegram();
      appendMessage('bot', '🎉 Thank you! Our expert will reach out to you soon.');
      currentStep = null;
    } else if (lowerInput === 'no') {
      appendMessage('bot', 'Okay, let\'s restart. May I know your name?');
      userInfo = { name: '', email: '', phone: '', urgency: '', service: '' };
      currentStep = 'name';
    } else {
      fallbackMessage();
    }

  } else {
    fallbackMessage();
  }
}

// Fallback message for unrecognized input
function fallbackMessage() {
  appendMessage('bot', '❗ Sorry, we didn’t understand that. You can also call us at 📞 +91 9008588030.');
}

// Submit collected info to backend
function sendLeadToTelegram() {
  fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userInfo)
  })
    .then(res => res.json())
    .then(data => {
      console.log("Lead submitted:", data);
    });
}

// 🎯 Tooltip popup logic on page load
window.addEventListener('load', () => {
  const tooltip = document.getElementById('chatbot-tooltip');
  const closeBtn = document.getElementById('tooltip-close');

  if (tooltip && closeBtn) {
    tooltip.classList.add('show');

    const autoHide = setTimeout(() => {
      tooltip.classList.remove('show');
    }, 6000);

    closeBtn.addEventListener('click', () => {
      tooltip.classList.remove('show');
      clearTimeout(autoHide);
    });
  }
});
