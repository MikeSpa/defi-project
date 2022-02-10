import React from 'react';
import { DAppProvider, Kovan } from '@usedapp/core';

function App() {
  return (
    <DAppProvider config={{
      networks: [Kovan],
      notifications: { //notifications
        expirationPeriod: 1000, //notif lasts 1sec
        checkInterval: 1000 //check every second
      }
    }}>
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
