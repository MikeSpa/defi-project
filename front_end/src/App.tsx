import { DAppProvider, Kovan } from '@usedapp/core';
import { Header } from "./components/Header";
import { Container } from "@material-ui/core"
import { Main } from "./components/Main"

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
      <br></br>
      <br></br>
      <Container maxWidth="md">
        <Main />
      </Container>
    </DAppProvider >

  );
}

export default App;
