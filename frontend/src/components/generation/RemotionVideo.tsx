'use client';

import React from 'react';
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';

interface Scene {
    id: string;
    type: 'title' | 'text' | 'math' | 'point_list';
    content?: string;
    items?: string[];
    physics?: 'bouncy' | 'smooth' | 'snappy';
    durationInSeconds: number;
}

interface RemotionVideoProps {
    scenes: Scene[];
}

// 1. Map physics profiles to Remotion spring configurations
const PHYSICS_CONFIGS = {
    bouncy: { stiffness: 100, damping: 10, mass: 1 },
    smooth: { stiffness: 50, damping: 20, mass: 1 },
    snappy: { stiffness: 200, damping: 20, mass: 0.5 },
};

export const RemotionVideo: React.FC<RemotionVideoProps> = ({ scenes = [] }) => {
    const { fps } = useVideoConfig();

    if (!scenes || scenes.length === 0) {
        return (
            <AbsoluteFill className="bg-black text-white flex items-center justify-center">
                <p className="text-4xl font-mono text-gray-500 uppercase tracking-widest">
                    [ No Scene Data Found ]
                </p>
            </AbsoluteFill>
        );
    }

    return (
        <AbsoluteFill className="bg-black text-white font-sans overflow-hidden">
            {scenes.map((scene, index) => {
                const startFrame = scenes
                    .slice(0, index)
                    .reduce((acc, s) => acc + (s.durationInSeconds || 5) * fps, 0);
                const durationFrames = (scene.durationInSeconds || 5) * fps;

                return (
                    <Sequence from={startFrame} durationInFrames={durationFrames} key={scene.id}>
                        <SceneRenderer scene={scene} />
                    </Sequence>
                );
            })}
        </AbsoluteFill>
    );
};

const SceneRenderer: React.FC<{ scene: Scene }> = ({ scene }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    
    // 2. Deterministic Entrance Physics
    const config = PHYSICS_CONFIGS[scene.physics || 'smooth'];
    const entrance = spring({
        frame,
        fps,
        config,
    });

    // 3. Entrance and Exit Fades (Frame-based)
    const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
    const translateY = interpolate(entrance, [0, 1], [30, 0]);

    return (
        <AbsoluteFill 
            style={{ 
                opacity, 
                transform: `translateY(${translateY}px)` 
            }} 
            className="flex flex-col items-center justify-center p-20 text-center"
        >
            {scene.type === 'title' && (
                <div style={{ transform: `scale(${entrance})` }}>
                   <h1 className="text-9xl font-bold tracking-tight mb-8">
                       {scene.content}
                   </h1>
                </div>
            )}

            {scene.type === 'text' && (
                <p className="text-6xl font-normal leading-relaxed max-w-6xl">
                    {scene.content}
                </p>
            )}

            {scene.type === 'math' && (
                <div className="text-8xl py-12" style={{ transform: `scale(${entrance})` }}>
                    <BlockMath math={scene.content || ''} />
                </div>
            )}

            {scene.type === 'point_list' && (
                <div className="space-y-10 text-left">
                    {scene.items?.map((item, i) => {
                        // 4. Staggered Entrance (also frame-deterministic)
                        const itemEntrance = spring({
                            frame: frame - (i * 5),
                            fps,
                            config,
                        });
                        
                        return (
                            <div 
                                key={i} 
                                style={{ 
                                    opacity: itemEntrance,
                                    transform: `translateX(${interpolate(itemEntrance, [0, 1], [40, 0])}px)`
                                }}
                                className="flex items-center gap-8 text-5xl"
                            >
                                <span className="text-gray-500 font-mono">0{i + 1}</span>
                                <span>{item}</span>
                            </div>
                        );
                    })}
                </div>
            )}
        </AbsoluteFill>
    );
};
