'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'

interface MannequinControlsProps {
  sendCommand: (command: string) => Promise<boolean>
  isConnected: boolean
}

interface SliderControlProps {
  label: string
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  step: number
  unit?: string
  disabled?: boolean
}

function SliderControl({ label, value, onChange, min, max, step, unit = '', disabled = false }: SliderControlProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-dark-300">{label}</label>
        <span className="text-sm text-primary-400 font-mono">{value.toFixed(3)}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        disabled={disabled}
        className="slider-input"
      />
    </div>
  )
}

interface CollapsibleSectionProps {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}

function CollapsibleSection({ title, children, defaultOpen = false }: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  
  return (
    <div className="card">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="text-xl font-bold text-primary-400">{title}</h3>
        {isOpen ? (
          <ChevronUpIcon className="h-5 w-5 text-primary-400" />
        ) : (
          <ChevronDownIcon className="h-5 w-5 text-primary-400" />
        )}
      </button>
      {isOpen && (
        <div className="mt-4">
          {children}
        </div>
      )}
    </div>
  )
}

export default function MannequinControls({ sendCommand, isConnected }: MannequinControlsProps) {
  // Camera state
  const [cameraPos, setCameraPos] = useState({ x: 0, y: 0, z: 0 })
  const [cameraRot, setCameraRot] = useState({ rx: 0, ry: 0, rz: 0 })
  const [continuousUpdate, setContinuousUpdate] = useState(true)
  
  // Character state
  const [skinTone, setSkinTone] = useState(0.75)
  const [hairColor, setHairColor] = useState({ r: 0.5, g: 0.3, b: 0.1 })
  const [eyeColor, setEyeColor] = useState(0.5)
  const [eyeSaturation, setEyeSaturation] = useState(100)
  
  // Bone sizes
  const [boneSizes, setBoneSizes] = useState({
    head: 1.0,
    chest: 1.0,
    hand: 1.0,
    abdomen: 1.0,
    arm: 1.0,
    leg: 1.0,
    feet: 1.0
  })
  
  // Character info
  const [characterName, setCharacterName] = useState('Lucy')
  
  const handleCameraUpdate = async (axis: string, value: number) => {
    if (axis.startsWith('r')) {
      setCameraRot(prev => ({ ...prev, [axis]: value }))
    } else {
      setCameraPos(prev => ({ ...prev, [axis]: value }))
    }
    
    if (continuousUpdate && isConnected) {
      const { x, y, z } = cameraPos
      const { rx, ry, rz } = cameraRot
      const command = `CAMSTREAM_${x.toFixed(3)}_${y.toFixed(3)}_${z.toFixed(3)}_${rx.toFixed(3)}_${ry.toFixed(3)}_${rz.toFixed(3)}`
      await sendCommand(command)
    }
  }
  
  const sendCameraCommand = async () => {
    const { x, y, z } = cameraPos
    const { rx, ry, rz } = cameraRot
    const command = `CAMSTREAM_${x.toFixed(3)}_${y.toFixed(3)}_${z.toFixed(3)}_${rx.toFixed(3)}_${ry.toFixed(3)}_${rz.toFixed(3)}`
    await sendCommand(command)
  }
  
  const resetCamera = () => {
    setCameraPos({ x: 0, y: 0, z: 0 })
    setCameraRot({ rx: 0, ry: 0, rz: 0 })
  }
  
  const handleSkinToneChange = async (value: number) => {
    setSkinTone(value)
    await sendCommand(`SKIN_${value.toFixed(2)}`)
  }
  
  const handleHairColorChange = async (color: 'r' | 'g' | 'b', value: number) => {
    const newColor = { ...hairColor, [color]: value }
    setHairColor(newColor)
    await sendCommand(`HAIR.${color.toUpperCase()}_${value.toFixed(2)}`)
  }
  
  const handleBoneSizeChange = async (bone: string, value: number) => {
    setBoneSizes(prev => ({ ...prev, [bone]: value }))
    const boneKey = bone.charAt(0).toUpperCase() + bone.slice(1)
    await sendCommand(`BONE.${boneKey}_${value.toFixed(2)}`)
  }
  
  const handleCharacterAction = async (action: string) => {
    switch (action) {
      case 'new':
        await sendCommand('NEW.Character')
        break
      case 'save':
        await sendCommand('BTN.Save')
        break
      case 'load':
        await sendCommand(`LOAD_${characterName}`)
        break
      case 'delete':
        await sendCommand(`DELETE_${characterName}`)
        break
      case 'setName':
        await sendCommand(`NAME_${characterName}`)
        break
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-primary-400">🎮 Mannequin Controls</h2>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
        </div>
      </div>
      
      {/* Camera System */}
      <CollapsibleSection title="📹 Camera System" defaultOpen={true}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Camera Shots */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Quick Camera Shots</h4>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Default', cmd: 'CAMSHOT.Default' },
                { label: 'Close Up', cmd: 'CAMSHOT.Close' },
                { label: 'Extreme Close', cmd: 'CAMSHOT.ExtremeClose' },
                { label: 'High Angle', cmd: 'CAMSHOT.HighAngle' },
                { label: 'Low Angle', cmd: 'CAMSHOT.LowAngle' },
                { label: 'Medium', cmd: 'CAMSHOT.Medium' },
                { label: 'Wide Shot', cmd: 'CAMSHOT.WideShot' },
                { label: 'Mobile Wide', cmd: 'CAMSHOT.MobileWideShot' }
              ].map(({ label, cmd }) => (
                <button
                  key={cmd}
                  onClick={() => sendCommand(cmd)}
                  disabled={!isConnected}
                  className="btn-secondary text-xs py-2"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          
          {/* View Types */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">View Types</h4>
            <div className="space-y-2">
              <button
                onClick={() => sendCommand('View.Desktop')}
                disabled={!isConnected}
                className="btn-primary w-full"
              >
                🖥️ Desktop View
              </button>
              <button
                onClick={() => sendCommand('View.Mobile')}
                disabled={!isConnected}
                className="btn-secondary w-full"
              >
                📱 Mobile View
              </button>
            </div>
          </div>
        </div>
        
        {/* Manual Camera Controls */}
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-white">Manual Camera Control</h4>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={continuousUpdate}
                onChange={(e) => setContinuousUpdate(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-dark-300">Real-time Updates</span>
            </label>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h5 className="text-md font-medium text-primary-300">Position (XYZ)</h5>
              <SliderControl
                label="X (Forward/Back)"
                value={cameraPos.x}
                onChange={(value) => handleCameraUpdate('x', value)}
                min={-1000}
                max={1000}
                step={0.001}
                disabled={!isConnected}
              />
              <SliderControl
                label="Y (Left/Right)"
                value={cameraPos.y}
                onChange={(value) => handleCameraUpdate('y', value)}
                min={-1000}
                max={1000}
                step={0.001}
                disabled={!isConnected}
              />
              <SliderControl
                label="Z (Up/Down)"
                value={cameraPos.z}
                onChange={(value) => handleCameraUpdate('z', value)}
                min={-1000}
                max={1000}
                step={0.001}
                disabled={!isConnected}
              />
            </div>
            
            <div className="space-y-4">
              <h5 className="text-md font-medium text-primary-300">Rotation (Pitch/Yaw/Roll)</h5>
              <SliderControl
                label="RX (Pitch)"
                value={cameraRot.rx}
                onChange={(value) => handleCameraUpdate('rx', value)}
                min={-180}
                max={180}
                step={0.001}
                unit="°"
                disabled={!isConnected}
              />
              <SliderControl
                label="RY (Yaw)"
                value={cameraRot.ry}
                onChange={(value) => handleCameraUpdate('ry', value)}
                min={-180}
                max={180}
                step={0.001}
                unit="°"
                disabled={!isConnected}
              />
              <SliderControl
                label="RZ (Roll)"
                value={cameraRot.rz}
                onChange={(value) => handleCameraUpdate('rz', value)}
                min={-180}
                max={180}
                step={0.001}
                unit="°"
                disabled={!isConnected}
              />
            </div>
          </div>
          
          <div className="flex justify-center space-x-4 mt-4">
            <button
              onClick={sendCameraCommand}
              disabled={!isConnected}
              className="btn-primary"
            >
              📷 Send Camera Position
            </button>
            <button
              onClick={resetCamera}
              disabled={!isConnected}
              className="btn-secondary"
            >
              🔄 Reset Camera
            </button>
          </div>
        </div>
      </CollapsibleSection>
      
      {/* Character Management */}
      <CollapsibleSection title="👤 Character Management">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Character Name</label>
              <input
                type="text"
                value={characterName}
                onChange={(e) => setCharacterName(e.target.value)}
                className="input-field w-full"
                placeholder="Enter character name"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleCharacterAction('new')}
                disabled={!isConnected}
                className="btn-primary"
              >
                ➕ New Character
              </button>
              <button
                onClick={() => handleCharacterAction('setName')}
                disabled={!isConnected}
                className="btn-secondary"
              >
                📝 Set Name
              </button>
              <button
                onClick={() => handleCharacterAction('save')}
                disabled={!isConnected}
                className="btn-secondary"
              >
                💾 Save
              </button>
              <button
                onClick={() => handleCharacterAction('load')}
                disabled={!isConnected}
                className="btn-secondary"
              >
                📂 Load
              </button>
            </div>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Character Presets</h4>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Masculine A', cmd: 'PRS.Masc' },
                { label: 'Masculine B', cmd: 'PRS.Masc1' },
                { label: 'Feminine A', cmd: 'PRS.Fem' },
                { label: 'Feminine B', cmd: 'PRS.Fem1' }
              ].map(({ label, cmd }) => (
                <button
                  key={cmd}
                  onClick={() => sendCommand(cmd)}
                  disabled={!isConnected}
                  className="btn-secondary text-sm"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CollapsibleSection>
      
      {/* Appearance Customization */}
      <CollapsibleSection title="✨ Appearance">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Outfits */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">👔 Outfits</h4>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Default', cmd: 'OF.Default' },
                { label: 'Maid Dress', cmd: 'OF.MaidDress' },
                { label: 'Pop Star', cmd: 'OF.PopStar' },
                { label: 'Kimono', cmd: 'OF.Kimono' },
                { label: 'Black Dress', cmd: 'OF.BlackDress' },
                { label: 'Space Suit', cmd: 'OF.SpaceSuit' },
                { label: 'Anime Armor', cmd: 'OF.ANIME' }
              ].map(({ label, cmd }) => (
                <button
                  key={cmd}
                  onClick={() => sendCommand(cmd)}
                  disabled={!isConnected}
                  className="btn-secondary text-xs py-2"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Hair Styles */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">💇 Hair Styles</h4>
            <div className="space-y-2">
              {[
                { label: 'Default Hair', cmd: 'HS.Default' },
                { label: 'Buzz Cut', cmd: 'HS.Buzz' },
                { label: 'Crop Cut', cmd: 'HS.Crop' }
              ].map(({ label, cmd }) => (
                <button
                  key={cmd}
                  onClick={() => sendCommand(cmd)}
                  disabled={!isConnected}
                  className="btn-secondary w-full text-sm"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Physical Attributes */}
        <div className="mt-6 space-y-6">
          {/* Skin Tone */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">🎨 Skin Tone</h4>
            <SliderControl
              label="Skin Tone"
              value={skinTone}
              onChange={handleSkinToneChange}
              min={0.03}
              max={1.2}
              step={0.01}
              disabled={!isConnected}
            />
          </div>
          
          {/* Hair Color */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">🎨 Hair Color (RGB)</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <SliderControl
                label="Red"
                value={hairColor.r}
                onChange={(value) => handleHairColorChange('r', value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Green"
                value={hairColor.g}
                onChange={(value) => handleHairColorChange('g', value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Blue"
                value={hairColor.b}
                onChange={(value) => handleHairColorChange('b', value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
            </div>
          </div>
          
          {/* Eye Customization */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">👁️ Eyes</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SliderControl
                label="Eye Color"
                value={eyeColor}
                onChange={(value) => setEyeColor(value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Eye Saturation"
                value={eyeSaturation}
                onChange={(value) => setEyeSaturation(value)}
                min={0}
                max={200}
                step={1}
                unit="%"
                disabled={!isConnected}
              />
            </div>
          </div>
        </div>
      </CollapsibleSection>
      
      {/* Body Proportions */}
      <CollapsibleSection title="🏃 Body Proportions">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(boneSizes).map(([bone, size]) => (
            <SliderControl
              key={bone}
              label={`${bone.charAt(0).toUpperCase()}${bone.slice(1)} Size`}
              value={size}
              onChange={(value) => handleBoneSizeChange(bone, value)}
              min={0}
              max={2}
              step={0.01}
              disabled={!isConnected}
            />
          ))}
        </div>
      </CollapsibleSection>
      
      {/* Facial Expressions */}
      <CollapsibleSection title="😊 Facial Expressions">
        <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {[
            { label: '😐 Neutral', cmd: 'FACE.Default' },
            { label: '😊 Happy', cmd: 'FACE.Happy' },
            { label: '😢 Sad', cmd: 'FACE.Sad' },
            { label: '😲 Surprised', cmd: 'FACE.Surprised' },
            { label: '😨 Fearful', cmd: 'FACE.Fearful' },
            { label: '🤔 Focused', cmd: 'FACE.Focused' },
            { label: '🤢 Disgusted', cmd: 'FACE.Disgusted' },
            { label: '😴 Tired', cmd: 'FACE.Tired' },
            { label: '😤 Annoyed', cmd: 'FACE.Annoyed' },
            { label: '😕 Confused', cmd: 'FACE.Confused' },
            { label: '🤨 Curious', cmd: 'FACE.Curious' },
            { label: '😳 Embarrassed', cmd: 'FACE.Embarrassed' },
            { label: '😠 Angry', cmd: 'FACE.Angry' },
            { label: '😑 Bored', cmd: 'FACE.Bored' },
            { label: '😌 Relaxed', cmd: 'FACE.Relaxed' },
            { label: '🤨 Suspicious', cmd: 'FACE.Suspicious' },
            { label: '😤 Proud', cmd: 'FACE.Proud' },
            { label: '😣 Pained', cmd: 'FACE.Pained' },
            { label: '😰 Nervous', cmd: 'FACE.Nervous' },
            { label: '😍 Love', cmd: 'FACE.Love' }
          ].map(({ label, cmd }) => (
            <button
              key={cmd}
              onClick={() => sendCommand(cmd)}
              disabled={!isConnected}
              className="btn-secondary text-xs py-2 px-1"
              title={label}
            >
              {label}
            </button>
          ))}
        </div>
      </CollapsibleSection>
      
      {/* Animations & Emotes */}
      <CollapsibleSection title="💃 Animations & Emotes">
        <div className="space-y-4">
          {/* Basic Animations */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Basic Animations</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              <button
                onClick={() => sendCommand('ANIM.Dance')}
                disabled={!isConnected}
                className="btn-primary"
              >
                💃 Dance
              </button>
              <button
                onClick={() => sendCommand('startspeaking')}
                disabled={!isConnected}
                className="btn-secondary"
              >
                🗣️ Start Speaking
              </button>
              <button
                onClick={() => sendCommand('stopspeaking')}
                disabled={!isConnected}
                className="btn-secondary"
              >
                🤐 Stop Speaking
              </button>
            </div>
          </div>
          
          {/* Emotes */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Emotes</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {[
                { label: '👋 Wave', cmd: 'EMOTE.Wave' },
                { label: '🫡 Salute', cmd: 'EMOTE.Salute' },
                { label: '🙇 Bow', cmd: 'EMOTE.Bow' },
                { label: '👍 Thumbs Up', cmd: 'EMOTE.TrumpThumbsUp' },
                { label: '🤫 Shush', cmd: 'EMOTE.Shushing' },
                { label: '🙏 Plead', cmd: 'EMOTE.Plead' },
                { label: '🤔 Ponder', cmd: 'EMOTE.Ponder' },
                { label: '😤 Show Money', cmd: 'EMOTE.ShowMeTheMoney' }
              ].map(({ label, cmd }) => (
                <button
                  key={cmd}
                  onClick={() => sendCommand(cmd)}
                  disabled={!isConnected}
                  className="btn-secondary text-xs py-2"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CollapsibleSection>
      
      {/* Environment */}
      <CollapsibleSection title="🏞️ Environment">
        <div>
          <h4 className="text-lg font-semibold text-white mb-3">Scene Levels</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {[
              { label: '🏠 Home', cmd: 'LVL.Home' },
              { label: '🎵 Lofi', cmd: 'LVL.Lofi' },
              { label: '🎧 DJ', cmd: 'LVL.DJ' },
              { label: '🏰 Medieval', cmd: 'LVL.Medieval' },
              { label: '🚀 Orbit', cmd: 'LVL.Orbit' },
              { label: '📺 Split Screen', cmd: 'LVL.Split' },
              { label: '📱 Triple Split', cmd: 'LVL.Split3' },
              { label: '🖥️ Quad Split', cmd: 'LVL.Split4' },
              { label: '🎓 Classroom', cmd: 'LVL.Classroom' }
            ].map(({ label, cmd }) => (
              <button
                key={cmd}
                onClick={() => sendCommand(cmd)}
                disabled={!isConnected}
                className="btn-secondary text-sm py-2"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  )
}