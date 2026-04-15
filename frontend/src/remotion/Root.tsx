import { registerRoot, Composition } from 'remotion';
import { RemotionVideo } from '../components/generation/RemotionVideo';

const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="Main"
        component={RemotionVideo}
        durationInFrames={1800} // Default 60s, will be overridden by CLI --frames
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ scenes: [] }}
      />
    </>
  );
};

registerRoot(RemotionRoot);
