const API_URL = "new-layout-nine.vercel.app/api/movies"; // Your deployed backend

async function loadMovies() {
  try {
    const auth = localStorage.getItem('hexa_auth');
    const response = await fetch(API_URL, {
      headers: { 'Authorization': auth }
    });
    
    if (!response.ok) throw new Error("Auth failed");
    renderMovies(await response.json());
  } catch (error) {
    showLoginModal();
  }
}

function showLoginModal() {
  // Implement a login popup that stores auth in localStorage
  const username = prompt("Admin Username:");
  const password = prompt("Admin Password:");
  localStorage.setItem('hexa_auth', 'Basic ' + btoa(`${username}:${password}`));
  loadMovies();
}

// Rest of your existing frontend code...
