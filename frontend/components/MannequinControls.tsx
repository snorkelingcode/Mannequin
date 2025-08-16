'use client'

import { useState, useCallback } from 'react'
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
  usePercentageStep?: boolean
}

function SliderControl({ 
  label, 
  value, 
  onChange, 
  min, 
  max, 
  step, 
  unit = '', 
  disabled = false,
  usePercentageStep = false
}: SliderControlProps) {
  const [localValue, setLocalValue] = useState(value)
  
  // Calculate percentage-based step (5% increments by default)
  const percentageStep = usePercentageStep ? (max - min) * 0.05 : step
  
  const handleChange = useCallback((newValue: number) => {
    setLocalValue(newValue)
    
    if (usePercentageStep) {
      // Only send command when reaching 5% increments
      const percentage = ((newValue - min) / (max - min)) * 100
      const roundedPercentage = Math.round(percentage / 5) * 5
      const actualValue = min + ((roundedPercentage / 100) * (max - min))
      
      if (Math.abs(newValue - actualValue) < percentageStep / 2) {
        onChange(actualValue)
      }
    } else {
      onChange(newValue)
    }
  }, [min, max, onChange, percentageStep, usePercentageStep])
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-neutral-200">{label}</label>
        <span className="text-sm text-primary-300 font-mono">
          {usePercentageStep ? `${Math.round(((localValue - min) / (max - min)) * 100)}%` : `${localValue.toFixed(3)}${unit}`}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={percentageStep}
        value={localValue}
        onChange={(e) => handleChange(parseFloat(e.target.value))}
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
        <h3 className="text-xl font-bold text-primary-300">{title}</h3>
        {isOpen ? (
          <ChevronUpIcon className="h-5 w-5 text-primary-300" />
        ) : (
          <ChevronDownIcon className="h-5 w-5 text-primary-300" />
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

// Separate component for primary controls (Camera, Appearance, Expressions)
export function PrimaryControls({ sendCommand, isConnected }: MannequinControlsProps) {
  
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

  // Morph targets state - ONLY actual codes from hooks.txt
  const [morphTargets, setMorphTargets] = useState({
    // Head
    headTop: 0.0,           // MTHT
    headSides: 0.0,         // MTHS
    headBack: 0.0,          // MTHB
    headBackWidth: 0.0,     // MTHBW
    // Neck
    neckFrontTop: 0.0,      // MTNFT
    neckFront: 0.0,         // MTNF
    neckSides: 0.0,         // MTNS
    neckBackHigh: 0.0,      // MTNBH
    neckBackLow: 0.0,       // MTNBL
    neckDefinition: 0.0,    // MTND
    // Ears
    earWidth: 0.0,          // MTEW
    earPoint: 0.0,          // MTEP
    earlobe: 0.0,           // MTEL
    earSize: 0.0,           // MTERS
    // Forehead/Temples
    foreheadCenter: 0.0,    // MTFHC
    foreheadCurvature: 0.0, // MTFHCR
    foreheadSides: 0.0,     // MTFHS
    temples: 0.0,           // MTT
    // Eyebrows
    eyebrowHeight: 0.0,     // MTEBH
    eyebrowWidth: 0.0,      // MTEBW
    eyebrowArch: 0.0,       // MTEBA
    // Eyes
    eyeCavity: 0.0,         // MTEC
    eyeWidth: 0.0,          // MTEYW
    eyeBags: 0.0,           // MTEB
    eyeHeight: 0.0,         // MTEYH
    // Nose
    noseBase: 0.0,          // MTNB
    noseLength: 0.0,        // MTNL
    noseWidth: 0.0,         // MTNW
    nostril: 0.0,           // MTN
    septum: 0.0,            // MTS
    noseCrookedness: 0.0,   // MTNCR
    // Cheeks
    cheekBone: 0.0,         // MTCB
    cheekTissue: 0.0,       // MTCT
    cheekDefinition: 0.0,   // MTCD
    // Lips
    lipsOuter: 0.0,         // MTLO
    lipsWidth: 0.0,         // MTLW
    lipsOverlap: 0.0,       // MTLOV
    lipsCurve: 0.0,         // MTLCV
    lipsDepth: 0.0,         // MTLD
    lipsUnderlap: 0.0,      // MTLU
    // Chin/Jaw
    chinLength: 0.0,        // MCL
    chinPoint: 0.0,         // MTCP
    chinWidth: 0.0,         // MTCW
    jawLower: 0.0,          // MTJL
    jawHigher: 0.0,         // MTJH
    // Other
    horns: 0.0              // MTH
  })
  
  const handleSkinToneChange = async (value: number) => {
    setSkinTone(value)
    // Use hooks.txt format: SKC.Float
    await sendCommand(`SKC.${value.toFixed(2)}`)
  }
  
  const handleHairColorChange = async (color: 'r' | 'g' | 'b', value: number) => {
    const newColor = { ...hairColor, [color]: value }
    setHairColor(newColor)
    // Use hooks.txt format: HCR.Float, HCG.Float, HCB.Float
    await sendCommand(`HC${color.toUpperCase()}.${value.toFixed(2)}`)
  }
  
  const handleBoneSizeChange = async (bone: string, value: number) => {
    setBoneSizes(prev => ({ ...prev, [bone]: value }))
    
    // Map bone names to ACTUAL hooks.txt bone codes
    const boneMap: { [key: string]: string } = {
      head: 'BNH',     // BNH.Float - Head size
      chest: 'BNC',    // BNC.Float - Chest size  
      hand: 'BNHD',    // BNHD.Float - Hand size
      abdomen: 'BNA',  // BNA.Float - Abdomen size
      arm: 'BNAR',     // BNAR.Float - Arm size
      leg: 'BNL',      // BNL.Float - Leg size
      feet: 'BNF'      // BNF.Float - Feet size
    }
    
    const boneCode = boneMap[bone]
    if (boneCode) {
      await sendCommand(`${boneCode}.${value.toFixed(2)}`)
    }
  }

  const handleEyeColorChange = async (value: number) => {
    setEyeColor(value)
    // Use hooks.txt format: EC.Float
    await sendCommand(`EC.${value.toFixed(2)}`)
  }

  const handleEyeSaturationChange = async (value: number) => {
    setEyeSaturation(value)
    // Use hooks.txt format: ES.Float
    await sendCommand(`ES.${value.toFixed(1)}`)
  }

  const handleMorphTargetChange = async (morphType: string, value: number) => {
    setMorphTargets(prev => ({ ...prev, [morphType]: value }))
    
    // Map frontend names to ACTUAL hooks.txt morph codes
    const morphMap: { [key: string]: string } = {
      // Head
      headTop: 'MTHT',
      headSides: 'MTHS',
      headBack: 'MTHB',
      headBackWidth: 'MTHBW',
      // Neck
      neckFrontTop: 'MTNFT',
      neckFront: 'MTNF',
      neckSides: 'MTNS',
      neckBackHigh: 'MTNBH',
      neckBackLow: 'MTNBL',
      neckDefinition: 'MTND',
      // Ears
      earWidth: 'MTEW',
      earPoint: 'MTEP',
      earlobe: 'MTEL',
      earSize: 'MTERS',
      // Forehead/Temples
      foreheadCenter: 'MTFHC',
      foreheadCurvature: 'MTFHCR',
      foreheadSides: 'MTFHS',
      temples: 'MTT',
      // Eyebrows
      eyebrowHeight: 'MTEBH',
      eyebrowWidth: 'MTEBW',
      eyebrowArch: 'MTEBA',
      // Eyes
      eyeCavity: 'MTEC',
      eyeWidth: 'MTEYW',
      eyeBags: 'MTEB',
      eyeHeight: 'MTEYH',
      // Nose
      noseBase: 'MTNB',
      noseLength: 'MTNL',
      noseWidth: 'MTNW',
      nostril: 'MTN',
      septum: 'MTS',
      noseCrookedness: 'MTNCR',
      // Cheeks
      cheekBone: 'MTCB',
      cheekTissue: 'MTCT',
      cheekDefinition: 'MTCD',
      // Lips
      lipsOuter: 'MTLO',
      lipsWidth: 'MTLW',
      lipsOverlap: 'MTLOV',
      lipsCurve: 'MTLCV',
      lipsDepth: 'MTLD',
      lipsUnderlap: 'MTLU',
      // Chin/Jaw
      chinLength: 'MCL',
      chinPoint: 'MTCP',
      chinWidth: 'MTCW',
      jawLower: 'MTJL',
      jawHigher: 'MTJH',
      // Other
      horns: 'MTH'
    }
    
    const morphCode = morphMap[morphType]
    if (morphCode) {
      await sendCommand(`${morphCode}.${value.toFixed(2)}`)
    }
  }
  
  return (
    <div className="space-y-6">
      
      {/* Appearance Customization */}
      <CollapsibleSection title="✨ Appearance" defaultOpen={true}>
        {/* Hair Styles */}
        <div>
          <h4 className="text-lg font-semibold text-neutral-100 mb-3">💇 Hair Styles</h4>
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
        
        {/* Physical Attributes */}
        <div className="mt-6 space-y-6">
          {/* Skin Tone */}
          <div>
            <h4 className="text-lg font-semibold text-neutral-100 mb-3">🎨 Skin Tone</h4>
            <SliderControl
              label="Skin Tone"
              value={skinTone}
              onChange={handleSkinToneChange}
              min={0.03}
              max={1.2}
              step={0.01}
              disabled={!isConnected}
              usePercentageStep={true}
            />
          </div>
          
          {/* Hair Color */}
          <div>
            <h4 className="text-lg font-semibold text-neutral-100 mb-3">🎨 Hair Color (RGB)</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <SliderControl
                label="Red"
                value={hairColor.r}
                onChange={(value) => handleHairColorChange('r', value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
                usePercentageStep={true}
              />
              <SliderControl
                label="Green"
                value={hairColor.g}
                onChange={(value) => handleHairColorChange('g', value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
                usePercentageStep={true}
              />
              <SliderControl
                label="Blue"
                value={hairColor.b}
                onChange={(value) => handleHairColorChange('b', value)}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
                usePercentageStep={true}
              />
            </div>
          </div>
          
          {/* Eye Customization */}
          <div>
            <h4 className="text-lg font-semibold text-neutral-100 mb-3">👁️ Eyes</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SliderControl
                label="Eye Color"
                value={eyeColor}
                onChange={handleEyeColorChange}
                min={0}
                max={1}
                step={0.01}
                disabled={!isConnected}
                usePercentageStep={true}
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
                usePercentageStep={true}
              />
            </div>
          </div>
        </div>
      </CollapsibleSection>
      
      {/* Facial Expressions */}
      <CollapsibleSection title="😊 Facial Expressions" defaultOpen={false}>
        <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 mb-2">
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
    </div>
  )
}

// Secondary controls component for advanced options
export function SecondaryControls({ sendCommand, isConnected }: MannequinControlsProps) {
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

  // Morph targets state - ONLY actual codes from hooks.txt
  const [morphTargets, setMorphTargets] = useState({
    // Head
    headTop: 0.0,           // MTHT
    headSides: 0.0,         // MTHS
    headBack: 0.0,          // MTHB
    headBackWidth: 0.0,     // MTHBW
    // Neck
    neckFrontTop: 0.0,      // MTNFT
    neckFront: 0.0,         // MTNF
    neckSides: 0.0,         // MTNS
    neckBackHigh: 0.0,      // MTNBH
    neckBackLow: 0.0,       // MTNBL
    neckDefinition: 0.0,    // MTND
    // Ears
    earWidth: 0.0,          // MTEW
    earPoint: 0.0,          // MTEP
    earlobe: 0.0,           // MTEL
    earSize: 0.0,           // MTERS
    // Forehead/Temples
    foreheadCenter: 0.0,    // MTFHC
    foreheadCurvature: 0.0, // MTFHCR
    foreheadSides: 0.0,     // MTFHS
    temples: 0.0,           // MTT
    // Eyebrows
    eyebrowHeight: 0.0,     // MTEBH
    eyebrowWidth: 0.0,      // MTEBW
    eyebrowArch: 0.0,       // MTEBA
    // Eyes
    eyeCavity: 0.0,         // MTEC
    eyeWidth: 0.0,          // MTEYW
    eyeBags: 0.0,           // MTEB
    eyeHeight: 0.0,         // MTEYH
    // Nose
    noseBase: 0.0,          // MTNB
    noseLength: 0.0,        // MTNL
    noseWidth: 0.0,         // MTNW
    nostril: 0.0,           // MTN
    septum: 0.0,            // MTS
    noseCrookedness: 0.0,   // MTNCR
    // Cheeks
    cheekBone: 0.0,         // MTCB
    cheekTissue: 0.0,       // MTCT
    cheekDefinition: 0.0,   // MTCD
    // Lips
    lipsOuter: 0.0,         // MTLO
    lipsWidth: 0.0,         // MTLW
    lipsOverlap: 0.0,       // MTLOV
    lipsCurve: 0.0,         // MTLCV
    lipsDepth: 0.0,         // MTLD
    lipsUnderlap: 0.0,      // MTLU
    // Chin/Jaw
    chinLength: 0.0,        // MCL
    chinPoint: 0.0,         // MTCP
    chinWidth: 0.0,         // MTCW
    jawLower: 0.0,          // MTJL
    jawHigher: 0.0,         // MTJH
    // Other
    horns: 0.0              // MTH
  })

  const handleBoneSizeChange = async (bone: string, value: number) => {
    setBoneSizes(prev => ({ ...prev, [bone]: value }))
    
    // Map bone names to ACTUAL hooks.txt bone codes
    const boneMap: { [key: string]: string } = {
      head: 'BNH',     // BNH.Float - Head size
      chest: 'BNC',    // BNC.Float - Chest size  
      hand: 'BNHD',    // BNHD.Float - Hand size
      abdomen: 'BNA',  // BNA.Float - Abdomen size
      arm: 'BNAR',     // BNAR.Float - Arm size
      leg: 'BNL',      // BNL.Float - Leg size
      feet: 'BNF'      // BNF.Float - Feet size
    }
    
    const boneCode = boneMap[bone]
    if (boneCode) {
      await sendCommand(`${boneCode}.${value.toFixed(2)}`)
    }
  }

  const handleMorphTargetChange = async (morphType: string, value: number) => {
    setMorphTargets(prev => ({ ...prev, [morphType]: value }))
    
    // Map frontend names to ACTUAL hooks.txt morph codes
    const morphMap: { [key: string]: string } = {
      // Head
      headTop: 'MTHT',
      headSides: 'MTHS',
      headBack: 'MTHB',
      headBackWidth: 'MTHBW',
      // Neck
      neckFrontTop: 'MTNFT',
      neckFront: 'MTNF',
      neckSides: 'MTNS',
      neckBackHigh: 'MTNBH',
      neckBackLow: 'MTNBL',
      neckDefinition: 'MTND',
      // Ears
      earWidth: 'MTEW',
      earPoint: 'MTEP',
      earlobe: 'MTEL',
      earSize: 'MTERS',
      // Forehead/Temples
      foreheadCenter: 'MTFHC',
      foreheadCurvature: 'MTFHCR',
      foreheadSides: 'MTFHS',
      temples: 'MTT',
      // Eyebrows
      eyebrowHeight: 'MTEBH',
      eyebrowWidth: 'MTEBW',
      eyebrowArch: 'MTEBA',
      // Eyes
      eyeCavity: 'MTEC',
      eyeWidth: 'MTEYW',
      eyeBags: 'MTEB',
      eyeHeight: 'MTEYH',
      // Nose
      noseBase: 'MTNB',
      noseLength: 'MTNL',
      noseWidth: 'MTNW',
      nostril: 'MTN',
      septum: 'MTS',
      noseCrookedness: 'MTNCR',
      // Cheeks
      cheekBone: 'MTCB',
      cheekTissue: 'MTCT',
      cheekDefinition: 'MTCD',
      // Lips
      lipsOuter: 'MTLO',
      lipsWidth: 'MTLW',
      lipsOverlap: 'MTLOV',
      lipsCurve: 'MTLCV',
      lipsDepth: 'MTLD',
      lipsUnderlap: 'MTLU',
      // Chin/Jaw
      chinLength: 'MCL',
      chinPoint: 'MTCP',
      chinWidth: 'MTCW',
      jawLower: 'MTJL',
      jawHigher: 'MTJH',
      // Other
      horns: 'MTH'
    }
    
    const morphCode = morphMap[morphType]
    if (morphCode) {
      await sendCommand(`${morphCode}.${value.toFixed(2)}`)
    }
  }

  return (
    <div className="space-y-6">
      {/* All controls moved to PrimaryControls for better organization */}
      <div className="text-center text-neutral-400 py-8">
        <p>Main controls are in the panel to the right →</p>
      </div>
    </div>
  )
}

// Default export for backward compatibility
export default function MannequinControls({ sendCommand, isConnected }: MannequinControlsProps) {
  return <PrimaryControls sendCommand={sendCommand} isConnected={isConnected} />
}
