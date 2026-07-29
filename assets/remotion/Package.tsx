import React from 'react';
import {AbsoluteFill} from 'remotion';

export type PackageTopic = {
  id: string;
  title: string;
  startSeconds: number;
  endSeconds: number;
};

export type PackageProps = {
  overlayOnly?: boolean;
  chapterIndex?: number;
  topics?: PackageTopic[];
  chapterStarts?: number[];
};

const ACCENTS = ['#8ee0ff', '#ffb38a', '#9dffc3', '#c4a8ff', '#ffd166', '#ff8ad1'];
const FONT = '"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif';

export const Package: React.FC<PackageProps> = ({
  overlayOnly = true,
  chapterIndex = 0,
  topics = [],
  chapterStarts = [],
}) => {
  if (!overlayOnly) throw new Error('Use the FFmpeg one-pass packaging path');
  if (!topics.length || topics.length !== chapterStarts.length - 1) {
    throw new Error('topics and progress segments must match');
  }
  const total = chapterStarts[chapterStarts.length - 1];
  const widths = topics.map((_, index) =>
    Math.round(((chapterStarts[index + 1] - chapterStarts[index]) / total) * 1828),
  );
  widths[widths.length - 1] += 1828 - widths.reduce((sum, width) => sum + width, 0);
  const accent = ACCENTS[chapterIndex % ACCENTS.length];
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent', fontFamily: FONT}}>
      <div style={{position:'absolute',left:42,top:38,display:'flex',overflow:'hidden',borderRadius:14,color:'#fff',background:'linear-gradient(135deg,rgba(13,18,27,.86),rgba(27,39,56,.72))',boxShadow:'0 10px 28px rgba(0,0,0,.24)'}}>
        <div style={{width:5,background:accent}} />
        <div style={{padding:'13px 20px 14px 16px'}}>
          <div style={{fontSize:17,fontWeight:800,letterSpacing:2.2,opacity:.72}}>CHAPTER {chapterIndex + 1}/{topics.length}</div>
          <div style={{marginTop:2,fontSize:30,fontWeight:850,letterSpacing:-.5}}>{topics[chapterIndex].title}</div>
        </div>
      </div>
      <div style={{position:'absolute',left:46,top:1022,width:1828,height:30,overflow:'hidden',borderRadius:999,border:'2px solid rgba(255,255,255,.14)',background:'rgba(13,18,27,.38)',boxSizing:'border-box',display:'flex'}}>
        {topics.map((topic, index) => (
          <div key={topic.id} style={{width:widths[index],height:'100%',boxSizing:'border-box',borderRight:index < topics.length - 1 ? '1px solid rgba(255,255,255,.20)' : 'none'}} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
