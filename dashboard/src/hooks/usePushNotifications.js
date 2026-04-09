"use client";

import { useEffect, useCallback } from "react";

/**
 * Hook to request notification permission and setup push notifications
 * Call this in your dashboard component on mount
 */
export default function usePushNotifications() {
  const requestNotificationPermission = useCallback(async () => {
    // Check browser support
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      console.log("Push notifications not supported in this browser");
      return false;
    }

    try {
      // Request permission
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        console.log("Notification permission denied");
        return false;
      }

      // Register service worker
      const registration = await navigator.serviceWorker.register("/sw.js", {
        scope: "/",
      });

      console.log("Service worker registered:", registration);

      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(
          process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
        ),
      });

      // Send subscription to backend
      const token = localStorage.getItem("visioniq_token") || localStorage.getItem("authToken") || localStorage.getItem("quantumeye_token");
      const response = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(subscription),
      });

      if (!response.ok) {
        console.error("Failed to save subscription to backend");
        return false;
      }

      console.log("Push subscription saved successfully");
      return true;
    } catch (error) {
      console.error("Failed to setup push notifications:", error);
      return false;
    }
  }, []);

  useEffect(() => {
    // Request permission on component mount if not already granted
    const permission = Notification.permission;
    if (permission === "default") {
      requestNotificationPermission();
    } else if (permission === "granted") {
      // Re-subscribe if already granted (in case of updates)
      requestNotificationPermission();
    }
  }, [requestNotificationPermission]);

  return { requestNotificationPermission };
}

/**
 * Convert VAPID public key from base64 to Uint8Array
 */
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/\-/g, "+").replace(/_/g, "/");

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }

  return outputArray;
}
