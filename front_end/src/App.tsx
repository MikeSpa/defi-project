import React from 'react';
import { DAppProvider, Kovan } from '@usedapp/core';
import { Header } from "./components/Header";
import { Header2 } from "./components/Header2";

function App() {
  return (
    <DAppProvider config={{
      networks: [Kovan],
      notifications: { //notifications
        expirationPeriod: 1000, //notif lasts 1sec
        checkInterval: 1000 //check every second
      }
    }}>
      <Header />
      <div>
        <p>
          DeFi project
        </p>
        <a
          href="https://github.com/MikeSpa/defi-project"
        >
          Project Github
        </a>
      </div>
    </DAppProvider>

  );
}

export default App;
