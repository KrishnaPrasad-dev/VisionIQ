// Service Worker for handling push notifications

self.addEventListener("push", (event) => {
  if (!event.data) {
    console.log("Push received but no data");
    return;
  }

  let data;
  try {
    data = event.data.json();
  } catch (e) {
    data = {
      title: "VisionIQ Alert",
      options: {
        body: event.data.text(),
      },
    };
  }

  const options = {
    icon: data.options?.icon || "/icon-192x192.png",
    badge: data.options?.badge || "/badge-72x72.png",
    tag: data.options?.tag || "visioniq-notification",
    requireInteraction: data.options?.requireInteraction !== false,
    data: data.options?.data || {},
    actions: [
      {
        action: "open",
        title: "View",
      },
      {
        action: "close",
        title: "Dismiss",
      },
    ],
  };

  const title = data.title || "VisionIQ Alert";

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "close") {
    return;
  }

  const urlToOpen = event.notification.data?.url || "/dashboard";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      // Check if dashboard is already open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === urlToOpen && "focus" in client) {
          return client.focus();
        }
      }
      // If not open, open it
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

self.addEventListener("notificationclose", (event) => {
  console.log("Notification dismissed:", event.notification.tag);
});
