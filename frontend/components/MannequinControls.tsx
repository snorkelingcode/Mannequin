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

  // Morph targets state
  const [morphTargets, setMorphTargets] = useState({
    // Head
    headTop: 0.0,
    headSides: 0.0,
    headBack: 0.0,
    headBackWidth: 0.0,
    // Face
    eyeWidth: 0.0,
    eyeHeight: 0.0,
    noseWidth: 0.0,
    noseLength: 0.0,
    lipsWidth: 0.0,
    chinLength: 0.0
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
    // Use hooks.txt format: HCR.Float, HCG.Float, HCB.Float
    await sendCommand(`HC${color.toUpperCase()}_${value.toFixed(2)}`)
  }
  
  const handleBoneSizeChange = async (bone: string, value: number) => {
    setBoneSizes(prev => ({ ...prev, [bone]: value }))
    const boneKey = bone.charAt(0).toUpperCase() + bone.slice(1)
    await sendCommand(`BONE.${boneKey}_${value.toFixed(2)}`)
  }

  const handleEyeColorChange = async (value: number) => {
    setEyeColor(value)
    // Use hooks.txt format: EC.Float
    await sendCommand(`EC_${value.toFixed(2)}`)
  }

  const handleEyeSaturationChange = async (value: number) => {
    setEyeSaturation(value)
    // Use hooks.txt format: ES.Float
    await sendCommand(`ES_${value.toFixed(1)}`)
  }

  const handleMorphTargetChange = async (morphType: string, value: number) => {
    setMorphTargets(prev => ({ ...prev, [morphType]: value }))
    
    // Map frontend names to hooks.txt morph codes
    const morphMap: { [key: string]: string } = {
      headTop: 'MTHT',
      headSides: 'MTHS', 
      headBack: 'MTHB',
      headBackWidth: 'MTHBW',
      eyeWidth: 'MTEYW',
      eyeHeight: 'MTEYH',
      noseWidth: 'MTNW',
      noseLength: 'MTNL',
      lipsWidth: 'MTLW',
      chinLength: 'MCL'
    }
    
    const morphCode = morphMap[morphType]
    if (morphCode) {
      await sendCommand(`${morphCode}_${value.toFixed(2)}`)
    }
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
      
      
      
      {/* Appearance Customization */}
      <CollapsibleSection title="✨ Appearance" defaultOpen={true}>
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
                onChange={handleEyeColorChange}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Eye Saturation"
                value={eyeSaturation}
                onChange={handleEyeSaturationChange}
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
                onClick={() => sendCommand('ANIM.Mannequin')}
                disabled={!isConnected}
                className="btn-secondary"
              >
                🧍 Mannequin Pose
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
      
      {/* Morph Targets */}
      <CollapsibleSection title="🎭 Morph Targets">
        <div className="space-y-6">
          {/* Head Morphs */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Head Structure</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SliderControl
                label="Head Top"
                value={morphTargets.headTop}
                onChange={(value) => handleMorphTargetChange('headTop', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Head Sides"
                value={morphTargets.headSides}
                onChange={(value) => handleMorphTargetChange('headSides', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Head Back"
                value={morphTargets.headBack}
                onChange={(value) => handleMorphTargetChange('headBack', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Head Back Width"
                value={morphTargets.headBackWidth}
                onChange={(value) => handleMorphTargetChange('headBackWidth', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
            </div>
          </div>
          
          {/* Facial Features */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Facial Features</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <SliderControl
                label="Eye Width"
                value={morphTargets.eyeWidth}
                onChange={(value) => handleMorphTargetChange('eyeWidth', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Eye Height"
                value={morphTargets.eyeHeight}
                onChange={(value) => handleMorphTargetChange('eyeHeight', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Nose Width"
                value={morphTargets.noseWidth}
                onChange={(value) => handleMorphTargetChange('noseWidth', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Nose Length"
                value={morphTargets.noseLength}
                onChange={(value) => handleMorphTargetChange('noseLength', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Lips Width"
                value={morphTargets.lipsWidth}
                onChange={(value) => handleMorphTargetChange('lipsWidth', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
              <SliderControl
                label="Chin Length"
                value={morphTargets.chinLength}
                onChange={(value) => handleMorphTargetChange('chinLength', value)}
                min={-1}
                max={1}
                step={0.01}
                disabled={!isConnected}
              />
            </div>
          </div>
        </div>
      </CollapsibleSection>
      
    </div>
  )
}