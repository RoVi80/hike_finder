import { createContext, useContext, useState } from "react";

const BackgroundContext = createContext();

export function BackgroundProvider({ children }) {
  const [bgImage, setBgImage] = useState("");

  return (
    <BackgroundContext.Provider value={{ bgImage, setBgImage }}>
      {children}
    </BackgroundContext.Provider>
  );
}

export function useBackground() {
  return useContext(BackgroundContext);
}
