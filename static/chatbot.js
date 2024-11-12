// Handle form submission
document.getElementById("chatForm").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevent the form from refreshing the page
    
    // Get the user input
    let user_input = document.getElementById("user_input").value;

    // Send the user input to the backend via POST request
    let response = await fetch("/chatbot", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            "user_input": user_input,
            'X-SECRET-KEY': 'I am Admin' // Include the secret key for security

        })
    });

    // Parse the response as JSON
    let result = await response.json();

    // Get the chatbot's response
    let botResponse = result.response;

    // Display the chatbot's response in the chatbox
    let messages = document.getElementById("messages");
    let userMessage = document.createElement("p");
    let botMessage = document.createElement("p");

    userMessage.innerText = "You: " + user_input;
    botMessage.innerText = "Bot: " + botResponse;

    messages.appendChild(userMessage);
    messages.appendChild(botMessage);

    // Clear the input field
    document.getElementById("user_input").value = "";
});
