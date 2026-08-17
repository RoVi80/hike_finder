import { Capacitor } from "@capacitor/core";

export const getBackendUrl = () => {
  const isNative = Capacitor.isNativePlatform();

  return isNative
    ? "http://192.168.1.6:8000"  // Android emulator to host machine
    : "http://localhost:8000"; // Web
};
