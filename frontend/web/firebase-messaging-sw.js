importScripts("https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyAn2pTrwrJjoTcXxjbtz0HaiPE5bCwsOOw",
  authDomain: "workmate-private-55afd.firebaseapp.com",
  projectId: "workmate-private-55afd",
  storageBucket: "workmate-private-55afd.firebasestorage.app",
  messagingSenderId: "1036924064365",
  appId: "1:1036924064365:web:7c008479cf2617d192e564",
  measurementId: "G-0WSYZPZ03J",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification ?? {};
  if (title) {
    self.registration.showNotification(title, { body: body ?? "" });
  }
});
