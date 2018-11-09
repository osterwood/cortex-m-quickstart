#![no_main]
#![no_std]
#![feature(extern_crate_item_prelude)]

extern crate cortex_m;
extern crate cortex_m_rt;
extern crate panic_halt;

extern crate stm32f4xx_hal as hal;

use cortex_m_rt::entry;
use cortex_m::peripheral::Peripherals;

use hal::delay::Delay;
use hal::prelude::*;
use hal::stm32;


#[entry]
fn main() -> ! {
    if let (Some(p), Some(cp)) = (stm32::Peripherals::take(), Peripherals::take()) {
        let gpioa = p.GPIOA.split();
        let gpiob = p.GPIOB.split();

        let mut led = gpioa.pa5.into_push_pull_output();

        // Constrain clock registers
        let mut rcc = p.RCC.constrain();

        let clocks = rcc.cfgr
				        .hclk(8.mhz())
				        .sysclk(84.mhz())
				        .freeze();

        // Get delay provider
        let mut delay = Delay::new(cp.SYST, clocks);

        loop {
            // Turn LED on
            led.set_high();

            // Delay twice for half a second due to limited timer resolution
            delay.delay_ms(500_u16);
            delay.delay_ms(500_u16);

            // Turn LED off
            led.set_low();

            // Delay twice for half a second due to limited timer resolution
            delay.delay_ms(500_u16);
            delay.delay_ms(500_u16);
        }
    }

    loop {
        continue;
    }
}