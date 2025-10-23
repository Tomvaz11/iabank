import { FlagsProvider } from './providers/flags';
import { RouterProvider } from './providers/router';
import { TelemetryProvider } from './providers/telemetry';

export const AppRoot = (): JSX.Element => (
  <TelemetryProvider>
    <FlagsProvider>
      <RouterProvider />
    </FlagsProvider>
  </TelemetryProvider>
);

export default AppRoot;
